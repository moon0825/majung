"""MCP 도구 13종 (07 시스템설계 §4).

자체 챗 UI(=MCP 호스트)가 이 도구들을 통해 모의 뱅킹 코어와 통신.
execute_remittance 는 오케스트레이터의 게이트 통과 후에만 호출됨(LLM 직접 호출 불가).
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Optional

from . import rules


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ── 수집 ──────────────────────────────────────────────────────
def get_account_balance(conn: sqlite3.Connection, user_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT balance_krw, is_limited_account, salary_months_consecutive "
        "FROM accounts WHERE user_id = ?", (user_id,),
    ).fetchone()
    if row is None:
        return {"found": False}
    return {
        "found": True,
        "balance_krw": row["balance_krw"],
        "is_limited_account": bool(row["is_limited_account"]),
        "salary_months_consecutive": row["salary_months_consecutive"],
    }


def detect_salary_deposit(conn: sqlite3.Connection, user_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT amount_krw, deposited_at FROM salary_events "
        "WHERE user_id = ? ORDER BY deposited_at DESC LIMIT 1", (user_id,),
    ).fetchone()
    acct = conn.execute(
        "SELECT salary_months_consecutive FROM accounts WHERE user_id = ?", (user_id,),
    ).fetchone()
    if row is None:
        return {"detected": False}
    return {
        "detected": True,
        "amount_krw": row["amount_krw"],
        "deposited_at": row["deposited_at"],
        "months_consecutive": acct["salary_months_consecutive"] if acct else 0,
    }


def get_fx_rate(conn: sqlite3.Connection, pair: str, window_days: int = 7) -> dict[str, Any]:
    """최신 = rate_now, 그 이전 window_days 일 평균 = rate_ma."""
    rows = conn.execute(
        "SELECT date, close_rate FROM fx_rates WHERE pair = ? ORDER BY date DESC", (pair,),
    ).fetchall()
    if not rows:
        return {"found": False}
    rate_now = rows[0]["close_rate"]
    window = rows[1 : 1 + window_days]
    rate_ma = sum(r["close_rate"] for r in window) / len(window) if window else rate_now
    return {"found": True, "pair": pair, "rate_now": rate_now, "rate_ma": round(rate_ma, 4)}


# ── Gate A, 위임장 검증 ──────────────────────────────────────
def validate_mandate(conn: sqlite3.Connection, mandate_id: str, intent: dict) -> dict[str, Any]:
    row = conn.execute(
        "SELECT json_blob, status, valid_until, revoked FROM mandates WHERE mandate_id = ?",
        (mandate_id,),
    ).fetchone()
    violations: list[str] = []
    if row is None:
        return {"valid": False, "violations": ["위임장 없음"]}

    blob = json.loads(row["json_blob"])
    if row["revoked"]:
        violations.append("철회된 위임장")
    if row["status"] != "active":
        violations.append(f"비활성 위임장({row['status']})")
    if row["valid_until"] and row["valid_until"] < _now_iso():
        violations.append("유효기간 만료")
    if not blob.get("esign", {}).get("esign_hash"):
        violations.append("전자서명 누락")

    # 범위 검증, 수취인이 화이트리스트에 있는지
    bnf_id = intent.get("bnf_id")
    whitelist_ids = {b["bnf_id"] for b in blob.get("beneficiary_whitelist", [])}
    in_scope = bnf_id in whitelist_ids if bnf_id else False

    return {
        "valid": not violations,
        "violations": violations,
        "in_mandate_scope": in_scope,
        "mandate": blob,
    }


# ── Gate B, Rule 한도·조건 ──────────────────────────────────
def check_limits(conn: sqlite3.Connection, mandate_id: str, amount_krw: int) -> dict[str, Any]:
    row = conn.execute(
        "SELECT json_blob FROM mandates WHERE mandate_id = ?", (mandate_id,),
    ).fetchone()
    if row is None:
        return {"within_limit": False, "reason": "위임장 없음"}
    limits = json.loads(row["json_blob"])["limits"]

    # 당월 누적 집행액
    month_prefix = datetime.now().strftime("%Y-%m")
    spent = conn.execute(
        "SELECT COALESCE(SUM(amount_krw),0) AS s FROM transactions "
        "WHERE user_id = (SELECT user_id FROM mandates WHERE mandate_id = ?) "
        "AND status = 'executed' AND created_at LIKE ?",
        (mandate_id, f"{month_prefix}%"),
    ).fetchone()["s"]

    per_tx_ok = amount_krw <= limits["limit_per_tx_krw"]
    monthly_ok = (spent + amount_krw) <= limits["limit_monthly_krw"]
    remaining = limits["limit_monthly_krw"] - spent
    return {
        "within_limit": per_tx_ok and monthly_ok,
        "remaining_monthly_krw": remaining,
        "per_tx_ok": per_tx_ok,
        "monthly_ok": monthly_ok,
    }


# ── Gate C, 수취인 화이트리스트 + AML ────────────────────────
_BLACKLIST_HINTS = ("otp", "비밀번호", "비번", "신분증", "선입금", "passport", "pin")


def screen_beneficiary_aml(
    conn: sqlite3.Connection,
    mandate_id: str,
    bnf_id: str,
    amount_krw: int,
    occurred_at: Optional[str] = None,
    in_mandate_scope: bool = True,
    memo: str = "",
) -> dict[str, Any]:
    when = datetime.fromisoformat(occurred_at) if occurred_at else datetime.now()
    bnf = conn.execute(
        "SELECT is_whitelisted, first_seen, name FROM beneficiaries WHERE bnf_id = ?",
        (bnf_id,),
    ).fetchone()

    is_whitelisted = bool(bnf["is_whitelisted"]) if bnf else False
    is_new = bnf is None or (bnf["first_seen"] is None)

    # 블랙리스트 키워드, 수취인 메모/패턴 매칭
    patterns = [r["keyword"].lower() for r in
                conn.execute("SELECT keyword FROM blacklist_patterns").fetchall()]
    haystack = (memo + " " + (bnf["name"] if bnf else "")).lower()
    hit_blacklist = any(p in haystack for p in patterns) or \
        any(h in haystack for h in _BLACKLIST_HINTS)

    ctx = rules.AmlContext(
        is_whitelisted=is_whitelisted,
        in_mandate_scope=in_mandate_scope,
        amount_krw=amount_krw,
        occurred_at=when,
        is_new_beneficiary=is_new,
        hit_blacklist=hit_blacklist,
    )
    decision = rules.evaluate_aml(ctx)
    return {
        "score": decision.score,
        "flags": decision.flags,
        "decision": decision.decision,
        "reason": decision.reason,
    }


# ── 행동 ──────────────────────────────────────────────────────
def execute_remittance(
    conn: sqlite3.Connection, mandate_id: str, bnf_id: str, amount_krw: int, fx_rate: float,
) -> dict[str, Any]:
    """게이트 PASS 후에만 호출됨. 한패스 레일은 모의 영수증으로 시뮬레이션."""
    user_id = conn.execute(
        "SELECT user_id FROM mandates WHERE mandate_id = ?", (mandate_id,),
    ).fetchone()["user_id"]
    tx_id = f"TX-{uuid.uuid4().hex[:10]}"
    conn.execute(
        "INSERT INTO transactions(tx_id, user_id, bnf_id, amount_krw, fx_rate, status, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (tx_id, user_id, bnf_id, amount_krw, fx_rate, "executed", _now_iso()),
    )
    conn.commit()
    return {"tx_id": tx_id, "status": "executed", "rail": "hanpass_mock"}


def notify_user(
    conn: sqlite3.Connection,
    user_id: str,
    lang: str,
    message: str,
    *,
    notify_type: str = "system",
    message_ko: str = "",
    tx_id: Optional[str] = None,
    mandate_id: Optional[str] = None,
    revocable: bool = True,
) -> dict[str, Any]:
    """건별 통지, 감사로그 + notifications 테이블에 동시 적재."""
    append_audit_log(conn, user_id, "notify", {"lang": lang, "message": message})
    # notifications 테이블에 적재 (GET /notifications/{user_id} 제공용)
    conn.execute(
        "INSERT INTO notifications"
        "(user_id, type, message_ko, message_local, tx_id, mandate_id, revocable, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (user_id, notify_type, message_ko or message, message,
         tx_id, mandate_id, int(revocable), _now_iso()),
    )
    conn.commit()
    return {"sent": True, "lang": lang, "message": message}


def revoke_mandate(conn: sqlite3.Connection, mandate_id: str) -> dict[str, Any]:
    conn.execute(
        "UPDATE mandates SET revoked = 1, status = 'revoked' WHERE mandate_id = ?",
        (mandate_id,),
    )
    conn.commit()
    return {"mandate_id": mandate_id, "revoked": True}


# ── 2막, 대환 가심사 ────────────────────────────────────────
def get_refi_offer(conn: sqlite3.Connection, user_id: str) -> dict[str, Any]:
    loan = conn.execute(
        "SELECT principal, apr, lender, remaining_months FROM loans_external "
        "WHERE user_id = ? ORDER BY principal DESC LIMIT 1", (user_id,),
    ).fetchone()
    product = conn.execute(
        "SELECT name, apr, max_term_months FROM refi_products ORDER BY apr ASC LIMIT 1",
    ).fetchone()
    user = conn.execute(
        "SELECT visa_expiry FROM users WHERE user_id = ?", (user_id,),
    ).fetchone()
    acct = conn.execute(
        "SELECT salary_months_consecutive FROM accounts WHERE user_id = ?", (user_id,),
    ).fetchone()
    if not (loan and product):
        return {"eligible": False, "reasons": ["사채/대환상품 데이터 없음"]}

    multi_debt = conn.execute(
        "SELECT COUNT(*) AS c FROM loans_external WHERE user_id = ?", (user_id,),
    ).fetchone()["c"]

    # 비자 잔여 개월 (대략)
    visa_remaining = 24
    if user and user["visa_expiry"]:
        try:
            d = datetime.fromisoformat(user["visa_expiry"])
            visa_remaining = max(0, (d - datetime.now()).days // 30)
        except ValueError:
            pass

    term = min(product["max_term_months"] or 36, loan["remaining_months"] or 36)
    result = rules.prescreen_refi(
        principal=loan["principal"],
        current_apr=loan["apr"],
        jb_apr=product["apr"],
        term_months=term,
        visa_remaining_months=visa_remaining,
        dsr=0.32,                       # 모의값
        multi_debt_count=multi_debt,
        salary_months_consecutive=acct["salary_months_consecutive"] if acct else 0,
    )
    return {
        "eligible": result.eligible,
        "reasons": result.reasons,
        "annual_saving_krw": result.annual_saving_krw,
        "new_monthly_krw": result.new_monthly_krw,
        "new_total_krw": result.new_total_krw,
        "late_fee_apr": result.late_fee_apr,
        "grade": result.grade,
        "decision": result.decision,
        "lender": loan["lender"],
        "current_apr": loan["apr"],
        "jb_product": product["name"],
        "jb_apr": product["apr"],
        "term_months": term,
    }


def refer_to_jb_engine(conn: sqlite3.Connection, user_id: str, refi_draft: dict) -> dict[str, Any]:
    """승인 아님, JB 심사엔진(모의)에 회부. 접수번호만 반환."""
    receipt = f"JB-REF-{uuid.uuid4().hex[:8]}"
    append_audit_log(conn, user_id, "refer_to_jb_engine",
                     {"receipt": receipt, "draft": refi_draft})
    return {"receipt_no": receipt, "status": "received_by_jb_engine"}


# ── 감사·STR ─────────────────────────────────────────────────
def append_audit_log(conn: sqlite3.Connection, user_id: str, event_type: str,
                     payload: dict) -> dict[str, Any]:
    cur = conn.execute(
        "INSERT INTO audit_log(user_id, event_type, payload_json, created_at) VALUES (?,?,?,?)",
        (user_id, event_type, json.dumps(payload, ensure_ascii=False), _now_iso()),
    )
    conn.commit()
    return {"log_id": cur.lastrowid}


def enqueue_str_candidate(conn: sqlite3.Connection, tx_id: Optional[str], score: int,
                          flags: list[str]) -> dict[str, Any]:
    cur = conn.execute(
        "INSERT INTO str_queue(tx_id, score, flags, status) VALUES (?,?,?,?)",
        (tx_id, score, json.dumps(flags, ensure_ascii=False), "queued"),
    )
    conn.commit()
    return {"queued": True, "str_id": cur.lastrowid}
