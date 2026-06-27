"""LLM 의도 파싱, 자연어만 담당. 실행권한 없음.

제1원칙: 이 모듈은 {intent, 추출 파라미터(후보)} 만 출력한다.
금액·실행 결정은 절대 못 한다, 그건 오케스트레이터의 3중 게이트 몫.

데모는 API 키 없이도 동작하도록 룰 기반 fallback 을 둔다.
본선에서 Claude(claude-opus-4-8 등)로 교체. 출력 스키마는 동일하게 유지한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ParsedIntent:
    intent: str                     # remit | hold_query | refi | revoke | create_mandate | unknown
    params: dict[str, Any] = field(default_factory=dict)
    raw: str = ""
    mandate_draft: Optional[dict] = None    # create_mandate 시에만 채워짐
    reply_ko: Optional[str] = None          # 한국어 안내 문구
    reply_local: Optional[str] = None       # 모국어(베트남어) 안내 문구


_REMIT_HINTS = ("보내", "송금", "gửi", "chuyển", "remit")
_REFI_HINTS = ("대출", "사채", "대환", "빚", "vay", "nợ")
_REVOKE_HINTS = ("취소", "철회", "그만", "hủy", "dừng")
# 위임장 생성 힌트, 한국어·베트남어 주요 패턴
_MANDATE_HINTS = ("위임", "자동 송금", "자동으로", "설정", "tự động", "ủy quyền",
                  "khi lương", "khi tỷ giá", "tối đa")

# 데모 고정 문장 파싱 패턴
# "Lương về thì gửi cho mẹ, khi tỷ giá tốt, tối đa 2 triệu"
_DEMO_SENTENCE_VI = "lương về thì gửi cho mẹ"
_DEMO_SENTENCE_KO = "급여 들어오면 엄마한테 보내"


def _build_mandate_draft(params: dict[str, Any], text: str) -> dict[str, Any]:
    """추출된 후보 파라미터로 시드 구조와 동일한 위임장 초안을 반환.

    실행 결정 없음, 후보 draft. 서명·저장은 /mandate/issue → /mandate/{id}/sign 경로.
    """
    limit_krw = params.get("amount_candidate_krw", 2_000_000)
    # 베트남어 "2 triệu" = 200만 KRW 매핑
    triệu_m = re.search(r"(\d+)\s*tri[eệ]u", text.lower())
    if triệu_m:
        limit_krw = int(triệu_m.group(1)) * 1_000_000

    return {
        "mandate_type": "remittance",
        "language": "vi",
        "beneficiary_whitelist": [
            {
                "bnf_id": "VN-BNF-01",
                "name": "Nguyen Thi Lan",
                "relation": "mother",
                "bank": "Vietcombank",
                "account_masked": "****8821",
            }
        ],
        "limits": {
            "limit_per_tx_krw": limit_krw,
            "limit_monthly_krw": limit_krw,
            "currency_target": "VND",
        },
        "trigger": {"type": "salary_in", "min_salary_krw": 500_000},
        "fx_condition": {
            "type": "better_than_ma",
            "window_days": 7,
            "threshold_pct": 1.0,
            "direction": "favorable",
        },
        "on_exception": "hold_and_ask",
        "ask_timeout_min": 720,
        "valid_until": "2026-12-31T23:59:59Z",
        "revocation": {"revocable": True, "revoked": False, "revoked_at": None},
        "notification": {"per_execution": True, "channel": "in_app_push", "language": "vi"},
    }


def parse_intent(text: str) -> ParsedIntent:
    """자연어 → 구조화 intent (실행 결정 없음).

    실제 LLM 연동 지점: 여기서 모델을 호출해 동일한 ParsedIntent 를 채운다.
    파싱된 금액/수취인은 어디까지나 '후보'이며, 게이트가 위임장으로 다시 검증한다.

    create_mandate 시 mandate_draft·reply_ko·reply_local 추가 반환.
    """
    t = text.lower()

    params: dict[str, Any] = {}
    # 금액 후보 추출 (예: "200만원", "5000000", "2 triệu")
    m = re.search(r"(\d+)\s*만", text)
    if m:
        params["amount_candidate_krw"] = int(m.group(1)) * 10_000
    else:
        m2 = re.search(r"(\d[\d,]{4,})", text)
        if m2:
            params["amount_candidate_krw"] = int(m2.group(1).replace(",", ""))

    if any(h in t for h in _REVOKE_HINTS):
        return ParsedIntent("revoke", params, text)
    if any(h in t for h in _REFI_HINTS):
        return ParsedIntent("refi", params, text)

    # 위임장 생성 의도, REMIT 힌트보다 먼저 검사(더 구체적)
    is_mandate = (
        any(h in t for h in _MANDATE_HINTS)
        or _DEMO_SENTENCE_VI in t
        or _DEMO_SENTENCE_KO in t
    )
    if is_mandate:
        draft = _build_mandate_draft(params, text)
        limit = draft["limits"]["limit_per_tx_krw"]
        reply_ko = (
            f"위임 조건을 확인했어요.\n"
            f"• 트리거: 급여 입금 시 + 7일평균 환율 대비 1% 이상 유리할 때\n"
            f"• 수취인: 어머니 Nguyen Thi Lan (Vietcombank ****8821)\n"
            f"• 한도: 1회·월 최대 {limit // 10_000}만원\n"
            f"• 철회권: 언제든 즉시 철회 가능\n"
            f"내용이 맞으면 서명해 주세요."
        )
        reply_local = (
            f"Đã xác nhận điều kiện ủy quyền.\n"
            f"• Khi nào: Nhận lương + tỷ giá tốt hơn TB 7 ngày ≥1%\n"
            f"• Người nhận: Mẹ Nguyen Thi Lan (Vietcombank ****8821)\n"
            f"• Hạn mức: tối đa {limit // 1_000_000} triệu / lần và / tháng\n"
            f"• Có thể hủy bất cứ lúc nào\n"
            f"Nếu đúng, vui lòng ký xác nhận."
        )
        return ParsedIntent(
            "create_mandate", params, text,
            mandate_draft=draft, reply_ko=reply_ko, reply_local=reply_local,
        )

    if any(h in t for h in _REMIT_HINTS):
        return ParsedIntent("remit", params, text)
    return ParsedIntent("unknown", params, text)
