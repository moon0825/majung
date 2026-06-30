"""parse_intent 출력 스키마 계약 테스트.

LLM 미연동 환경(fallback rule-based)에서도 그린이어야 한다.
ParsedIntent 필드·타입·값 집합을 검증하며, 실행 경로에 영향을 주지 않는다.
"""
from app.llm import ParsedIntent, parse_intent

VALID_INTENTS = {"remit", "hold_query", "refi", "revoke", "create_mandate", "unknown"}


# ── 필드 존재·타입 계약 ─────────────────────────────────────────────────────

def test_schema_has_required_fields():
    result = parse_intent("hello")
    assert hasattr(result, "intent")
    assert hasattr(result, "params")
    assert hasattr(result, "raw")
    assert hasattr(result, "mandate_draft")
    assert hasattr(result, "reply_ko")
    assert hasattr(result, "reply_local")


def test_intent_is_valid_enum():
    for text in ["보내줘", "대출", "취소", "Lương về thì gửi cho mẹ", "anything else"]:
        r = parse_intent(text)
        assert r.intent in VALID_INTENTS, f"unexpected intent '{r.intent}' for text '{text}'"


def test_params_is_always_dict():
    for text in ["보내줘 200만원", "대환", "", "gibberish"]:
        assert isinstance(parse_intent(text).params, dict)


def test_raw_preserves_input():
    text = "월급 들어오면 엄마한테 보내"
    r = parse_intent(text)
    assert r.raw == text


# ── 개별 intent 라우팅 계약 ─────────────────────────────────────────────────

def test_remit_intent_detected():
    r = parse_intent("지금 200만원 보내줘")
    assert r.intent == "remit"


def test_refi_intent_detected():
    r = parse_intent("사채 대환하고 싶어")
    assert r.intent == "refi"


def test_revoke_intent_detected():
    r = parse_intent("위임 취소해줘")
    assert r.intent == "revoke"


def test_create_mandate_vi_sentence_detected():
    r = parse_intent("Lương về thì gửi cho mẹ, khi tỷ giá tốt, tối đa 2 triệu.")
    assert r.intent == "create_mandate"


def test_unknown_falls_back():
    r = parse_intent("날씨가 어때요")
    assert r.intent == "unknown"


# ── create_mandate 드래프트 구조 계약 ─────────────────────────────────────

def test_create_mandate_fills_draft():
    r = parse_intent("Lương về thì gửi cho mẹ, khi tỷ giá tốt, tối đa 2 triệu.")
    assert r.mandate_draft is not None
    d = r.mandate_draft
    assert d["mandate_type"] == "remittance"
    assert "beneficiary_whitelist" in d
    assert len(d["beneficiary_whitelist"]) >= 1
    assert d["revocation"]["revocable"] is True


def test_create_mandate_fills_reply_texts():
    r = parse_intent("Lương về thì gửi cho mẹ, khi tỷ giá tốt, tối đa 2 triệu.")
    assert r.reply_ko and "한도" in r.reply_ko
    assert r.reply_local and "Hạn mức" in r.reply_local


def test_non_mandate_intent_has_no_draft():
    for text in ["보내줘", "대환", "취소"]:
        r = parse_intent(text)
        assert r.mandate_draft is None, f"mandate_draft should be None for intent '{r.intent}'"


# ── amount_candidate 추출 계약 ─────────────────────────────────────────────

def test_amount_candidate_extracted_from_korean():
    r = parse_intent("150만원 보내줘")
    assert r.params.get("amount_candidate_krw") == 1_500_000


def test_amount_candidate_none_when_absent():
    r = parse_intent("대출 받고 싶어")
    assert "amount_candidate_krw" not in r.params or r.params.get("amount_candidate_krw") is None
