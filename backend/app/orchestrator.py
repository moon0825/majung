"""오케스트레이터, 3중 게이트를 강제하는 유일한 송금 실행 경로.

제1원칙: LLM은 execute_remittance 를 직접 호출할 수 없다.
반드시 Gate A(위임검증) → Gate B(Rule 한도·FX) → Gate C(AML) 순서를 통과해야 한다.
판단 → 행동 → 검증/개선 (평가 용어 그대로).
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any, Optional

from . import mcp_tools


@dataclass
class GateTrace:
    gate: str                       # "A" | "B" | "C"
    label: str
    passed: bool
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class RemittanceOutcome:
    status: str                     # executed | held | str_hold | blocked | rejected
    message_ko: str
    message_local: str
    traces: list[GateTrace] = field(default_factory=list)
    tx_id: Optional[str] = None


# 모국어(베트남어) 고정 통지 문구 (데모용)
MSG = {
    "executed": ("환율이 좋아 어머니께 자동 송금했어요.",
                 "Đã tự động gửi tiền cho mẹ vì tỷ giá tốt."),
    "held": ("정말 보내려는 분이 맞습니까? 잠시 보류했어요.",
             "Bạn có chắc muốn gửi cho người này không? Đã tạm giữ."),
    "str_hold": ("의심 거래로 보류하고 검토 대기열에 넣었어요.",
                 "Giao dịch nghi ngờ, đã tạm giữ và đưa vào hàng đợi kiểm tra."),
    "blocked": ("비밀번호와 OTP는 절대 알려주지 마세요. 거래를 차단했습니다.",
                "Đừng bao giờ cung cấp mật khẩu/OTP. Đã chặn."),
    "wait_fx": ("환율이 아직 조건에 못 미쳐 기다리는 중이에요.",
                "Tỷ giá chưa đạt điều kiện, đang chờ."),
    "rejected": ("위임 범위를 벗어나 실행하지 않았어요.",
                 "Ngoài phạm vi ủy quyền, không thực hiện."),
}


def run_remittance(
    conn: sqlite3.Connection,
    *,
    mandate_id: str,
    bnf_id: str,
    amount_krw: int,
    fx_pair: str = "KRW/VND",
    occurred_at: Optional[str] = None,
    memo: str = "",
) -> RemittanceOutcome:
    """위임 송금 1막 e2e. 게이트 PASS 시에만 execute_remittance 호출."""
    traces: list[GateTrace] = []
    intent = {"bnf_id": bnf_id, "amount_krw": amount_krw}
    user_id_row = conn.execute(
        "SELECT user_id FROM mandates WHERE mandate_id = ?", (mandate_id,),
    ).fetchone()
    user_id = user_id_row["user_id"] if user_id_row else None

    def _log(event: str, payload: dict) -> None:
        if user_id:
            mcp_tools.append_audit_log(conn, user_id, event, payload)

    # ── Gate A, 위임장 검증 ──
    a = mcp_tools.validate_mandate(conn, mandate_id, intent)
    traces.append(GateTrace("A", "위임장 검증 (Mandate Validation)", a["valid"], a))
    _log("gate_a", a)
    if not a["valid"]:
        return RemittanceOutcome("rejected", *MSG["rejected"], traces=traces)

    in_scope = a.get("in_mandate_scope", False)
    fx = mcp_tools.get_fx_rate(conn, fx_pair, window_days=7)

    # ── Gate B, Rule 한도 + FX 조건 ──
    # 위임 범위 밖(신규 수취인 등) 시도는 여기서 하드 거절하지 않고 on_exception=hold_and_ask
    # 정책에 따라 Gate C(AML)로 넘겨 보류/STR 판정한다. 한도·FX는 자동집행(in-scope)에만 적용.
    if in_scope:
        limits = mcp_tools.check_limits(conn, mandate_id, amount_krw)
        from .rules import evaluate_fx
        mandate_fx = a["mandate"]["fx_condition"]
        fx_decision = evaluate_fx(fx["rate_now"], fx["rate_ma"],
                                  threshold_pct=mandate_fx["threshold_pct"])
        b_detail = {"limits": limits, "fx": fx, "fx_decision": fx_decision.__dict__}
        b_pass = limits["within_limit"] and fx_decision.decision == "TRIGGER_EXECUTE"
        traces.append(GateTrace("B", "Rule 한도·조건 (Rule Limits)", b_pass, b_detail))
        _log("gate_b", b_detail)
        if not limits["within_limit"]:
            return RemittanceOutcome("rejected", *MSG["rejected"], traces=traces)
        if fx_decision.decision != "TRIGGER_EXECUTE":
            return RemittanceOutcome("held", *MSG["wait_fx"], traces=traces)
    else:
        b_detail = {"skipped": "위임 범위 밖, on_exception=hold_and_ask → AML로 회부"}
        traces.append(GateTrace("B", "Rule 한도·조건 (Rule Limits)", False, b_detail))
        _log("gate_b", b_detail)

    # ── Gate C, 화이트리스트 + AML ──
    aml = mcp_tools.screen_beneficiary_aml(
        conn, mandate_id, bnf_id, amount_krw,
        occurred_at=occurred_at, in_mandate_scope=in_scope, memo=memo,
    )
    c_pass = aml["decision"] == "PASS"
    traces.append(GateTrace("C", "수취인 화이트리스트 + AML 스크리닝", c_pass, aml))
    _log("gate_c", aml)

    if aml["decision"] == "BLOCK":
        return RemittanceOutcome("blocked", *MSG["blocked"], traces=traces)
    if aml["decision"] == "STR_HOLD":
        mcp_tools.enqueue_str_candidate(conn, None, aml["score"], aml["flags"])
        return RemittanceOutcome("str_hold", *MSG["str_hold"], traces=traces)
    if aml["decision"] == "HOLD":
        return RemittanceOutcome("held", *MSG["held"], traces=traces)

    # 위임 범위 밖은 AML PASS여도 자동 실행 금지, 모국어 확인 보류(hold_and_ask)
    if not in_scope:
        return RemittanceOutcome("held", *MSG["held"], traces=traces)

    # ── 행동, 게이트 전부 PASS → 실행 ──
    tx = mcp_tools.execute_remittance(conn, mandate_id, bnf_id, amount_krw, fx["rate_now"])
    lang = a["mandate"].get("language", "vi")
    mcp_tools.notify_user(
        conn, user_id, lang, MSG["executed"][1],
        notify_type="executed",
        message_ko=MSG["executed"][0],
        tx_id=tx["tx_id"],
        mandate_id=mandate_id,
        revocable=True,
    )
    _log("execute", {"tx_id": tx["tx_id"], "amount_krw": amount_krw})
    return RemittanceOutcome("executed", *MSG["executed"], traces=traces, tx_id=tx["tx_id"])
