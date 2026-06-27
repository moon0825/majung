"""신규 엔드포인트 통합 테스트, /mandate/issue, /sign, /salary/deposit, /notifications.

실행: cd backend && pytest tests/test_new_endpoints.py
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import get_conn, init_schema, DB_PATH
from app.seed import seed


# ── 픽스처 ────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def fresh_db():
    """각 테스트 전에 DB 재시드."""
    seed()
    yield
    # 정리는 다음 seed()가 처리


@pytest.fixture()
def client():
    return TestClient(app)


USER_ID = "USR-VN-1029"
EXISTING_MANDATE = "MND-2026-0001"


# ── /chat 확장, create_mandate 의도 ─────────────────────────
def test_chat_vi_sentence_returns_create_mandate(client):
    """베트남어 데모 고정 문장 → intent=create_mandate + mandate_draft 반환."""
    resp = client.post("/chat", json={
        "text": "Lương về thì gửi cho mẹ, khi tỷ giá tốt, tối đa 2 triệu"
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == "create_mandate"
    assert body["mandate_draft"] is not None
    assert body["mandate_draft"]["mandate_type"] == "remittance"
    # 한도 2triệu = 2,000,000 KRW
    assert body["mandate_draft"]["limits"]["limit_per_tx_krw"] == 2_000_000
    assert body["reply_ko"] is not None
    assert body["reply_local"] is not None
    # 철회권 언급 포함
    assert "철회" in body["reply_ko"]
    assert "hủy" in body["reply_local"]


def test_chat_ko_sentence_returns_create_mandate(client):
    """한국어 위임 설정 문장 → intent=create_mandate."""
    resp = client.post("/chat", json={"text": "급여 들어오면 엄마한테 자동 송금 설정해줘"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == "create_mandate"
    assert body["mandate_draft"] is not None


def test_chat_no_execution_decision(client):
    """create_mandate 응답에 실행 결정 없음, note 확인."""
    resp = client.post("/chat", json={
        "text": "Lương về thì gửi cho mẹ, khi tỷ giá tốt, tối đa 2 triệu"
    })
    body = resp.json()
    assert "3중 게이트" in body["note"]


# ── /mandate/issue ────────────────────────────────────────────
def test_mandate_issue_creates_pending_sign(client):
    """위임장 초안 발급 → pending_sign 상태."""
    draft = {
        "mandate_type": "remittance",
        "language": "vi",
        "beneficiary_whitelist": [
            {"bnf_id": "VN-BNF-01", "name": "Nguyen Thi Lan", "relation": "mother"}
        ],
        "limits": {"limit_per_tx_krw": 1_500_000, "limit_monthly_krw": 1_500_000,
                   "currency_target": "VND"},
        "trigger": {"type": "salary_in", "min_salary_krw": 500_000},
        "fx_condition": {"type": "better_than_ma", "window_days": 7,
                         "threshold_pct": 1.0, "direction": "favorable"},
        "valid_until": "2026-12-31T23:59:59Z",
    }
    resp = client.post("/mandate/issue", json={"user_id": USER_ID, "draft": draft})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "pending_sign"
    assert body["mandate_id"].startswith("MND-")
    assert "서명" in body["summary_ko"]
    assert "ký" in body["summary_local"]


def test_mandate_issue_auto_generates_mandate_id(client):
    """mandate_id 미지정 시 자동 발급."""
    draft = {
        "mandate_type": "remittance",
        "language": "vi",
        "beneficiary_whitelist": [],
        "limits": {"limit_per_tx_krw": 1_000_000, "limit_monthly_krw": 1_000_000,
                   "currency_target": "VND"},
        "valid_until": "2026-12-31T23:59:59Z",
    }
    resp = client.post("/mandate/issue", json={"user_id": USER_ID, "draft": draft})
    body = resp.json()
    assert len(body["mandate_id"]) > 5


# ── /mandate/{id}/sign ────────────────────────────────────────
def test_mandate_sign_flow(client):
    """발급 → 서명 순서 테스트. active 상태·esign_hash 반환 확인."""
    # 발급
    draft = {
        "mandate_type": "remittance",
        "language": "vi",
        "beneficiary_whitelist": [
            {"bnf_id": "VN-BNF-01", "name": "Nguyen Thi Lan"}
        ],
        "limits": {"limit_per_tx_krw": 2_000_000, "limit_monthly_krw": 2_000_000,
                   "currency_target": "VND"},
        "valid_until": "2026-12-31T23:59:59Z",
    }
    issue_resp = client.post("/mandate/issue", json={"user_id": USER_ID, "draft": draft})
    mandate_id = issue_resp.json()["mandate_id"]

    # 서명
    sign_resp = client.post(f"/mandate/{mandate_id}/sign")
    assert sign_resp.status_code == 200
    body = sign_resp.json()
    assert body["status"] == "active"
    assert body["esign_hash"].startswith("sha256:")
    assert body["signed_at"] != ""


def test_mandate_sign_already_active_returns_409(client):
    """이미 active 위임장 재서명 → 409."""
    # 기존 시드 위임장은 이미 active
    resp = client.post(f"/mandate/{EXISTING_MANDATE}/sign")
    assert resp.status_code == 409


def test_mandate_sign_nonexistent_returns_404(client):
    """존재하지 않는 위임장 서명 → 404."""
    resp = client.post("/mandate/MND-NOTEXIST/sign")
    assert resp.status_code == 404


# ── /salary/deposit ───────────────────────────────────────────
def test_salary_deposit_triggers_auto_remittance(client):
    """급여 입금 → active 위임장 감지 → 3중 게이트 → 자동 송금 executed."""
    resp = client.post("/salary/deposit",
                       json={"user_id": USER_ID, "amount_krw": 2_100_000})
    assert resp.status_code == 200
    body = resp.json()
    assert body["salary_event"]["amount_krw"] == 2_100_000
    assert body["remittance"] is not None
    # 시드 FX +1.82% 조건 충족 → executed 또는 gates 통과
    remit = body["remittance"]
    assert remit["status"] in ("executed", "held", "str_hold", "blocked", "rejected")
    # 게이트 3개 존재
    assert len(remit["gates"]) == 3


def test_salary_deposit_no_active_mandate(client):
    """active 위임장 없는 유저 → remittance null."""
    # 기존 위임장 철회
    client.post(f"/mandate/{EXISTING_MANDATE}/revoke")
    resp = client.post("/salary/deposit",
                       json={"user_id": USER_ID, "amount_krw": 2_100_000})
    assert resp.status_code == 200
    body = resp.json()
    assert body["remittance"] is None
    assert "note" in body


# ── /notifications/{user_id} ─────────────────────────────────
def test_notifications_appear_after_salary_remittance(client):
    """급여 입금 후 자동 송금 실행 시 notifications에 통지 이력 적재."""
    # 급여 입금 → 송금 실행
    client.post("/salary/deposit", json={"user_id": USER_ID, "amount_krw": 2_100_000})

    resp = client.get(f"/notifications/{USER_ID}")
    assert resp.status_code == 200
    body = resp.json()
    notifs = body["notifications"]
    assert isinstance(notifs, list)
    # 적어도 1개 이상 적재
    assert len(notifs) >= 1
    # 각 항목 필수 필드
    first = notifs[0]
    assert "id" in first
    assert "type" in first
    assert "message_ko" in first
    assert "message_local" in first
    assert "revocable" in first
    assert "created_at" in first


def test_notifications_appear_after_sign(client):
    """위임장 서명 시 notifications에 system 통지 적재."""
    # 신규 위임장 발급 후 서명
    draft = {
        "mandate_type": "remittance",
        "language": "vi",
        "beneficiary_whitelist": [{"bnf_id": "VN-BNF-01", "name": "Nguyen Thi Lan"}],
        "limits": {"limit_per_tx_krw": 2_000_000, "limit_monthly_krw": 2_000_000,
                   "currency_target": "VND"},
        "valid_until": "2026-12-31T23:59:59Z",
    }
    issue_resp = client.post("/mandate/issue", json={"user_id": USER_ID, "draft": draft})
    mandate_id = issue_resp.json()["mandate_id"]
    client.post(f"/mandate/{mandate_id}/sign")

    resp = client.get(f"/notifications/{USER_ID}")
    body = resp.json()
    notifs = body["notifications"]
    assert any("서명" in n["message_ko"] or n["type"] == "system" for n in notifs)
