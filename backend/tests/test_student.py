"""v2 유학생 세그먼트 통합 테스트 — 추가만, 기존 20건과 격리(user-scoped).

대상:
  POST /student/tuition/execute       , 등록금 외화 송금(KRW/CNY) — 동일 3중 게이트 재사용
  GET  /account/limit-status/{user}   , 한도계좌 → 정식계좌 승급 코치(read-only)
  GET  /student/credit-profile/{user} , 재학중 신용형성 스냅샷(read-only)

실행: cd backend && pytest tests/test_student.py
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import activation
from app.main import app
from app.seed import (
    STUDENT_BNF_ID,
    STUDENT_ID,
    STUDENT_MANDATE_ID,
    STUDENT_TUITION_KRW,
    seed,
)

WORKER_ID = "USR-VN-1029"


@pytest.fixture(autouse=True)
def fresh_db():
    seed()
    yield


@pytest.fixture()
def client():
    return TestClient(app)


# ── 결정적 판정 함수 (DB 불필요) ──────────────────────────────
def test_limit_release_eligible_at_three_months():
    r = activation.evaluate_limit_release(
        is_limited_account=True, salary_months_consecutive=3)
    assert r.eligible
    assert r.status == "eligible"
    assert r.remaining_months == 0


def test_limit_release_in_progress_below_threshold():
    r = activation.evaluate_limit_release(
        is_limited_account=True, salary_months_consecutive=1)
    assert not r.eligible
    assert r.status == "in_progress"
    assert r.remaining_months == 2


def test_limit_release_full_account_when_not_limited():
    r = activation.evaluate_limit_release(
        is_limited_account=False, salary_months_consecutive=12)
    assert not r.eligible
    assert r.status == "full_account"


# ── ① 등록금 송금 (실동작) ───────────────────────────────────
def test_tuition_executes_through_three_gates(client):
    """KRW/CNY +1.846% → 화이트리스트 대학 → 3중 게이트 통과 → executed."""
    resp = client.post("/student/tuition/execute", json={
        "mandate_id": STUDENT_MANDATE_ID,
        "bnf_id": STUDENT_BNF_ID,
        "amount_krw": STUDENT_TUITION_KRW,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "executed"
    assert body["tx_id"] is not None
    # 3중 게이트 전부 존재·통과
    assert len(body["gates"]) == 3
    assert all(g["passed"] for g in body["gates"])
    # Gate B 가 FX 조건(≥1%)으로 통과했는지 확인
    assert body["gates"][1]["passed"] is True


def test_tuition_out_of_scope_recipient_not_executed(client):
    """위임 범위 밖 수취인은 자동 실행되지 않는다(보류). 게이트 우회 불가 확인."""
    resp = client.post("/student/tuition/execute", json={
        "mandate_id": STUDENT_MANDATE_ID,
        "bnf_id": "CN-UNKNOWN-99",
        "amount_krw": STUDENT_TUITION_KRW,
    })
    assert resp.status_code == 200
    assert resp.json()["status"] != "executed"


# ── ② 한도해제 코치 (실동작 read-only) ──────────────────────
def test_limit_status_student_eligible(client):
    resp = client.get(f"/account/limit-status/{STUDENT_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_limited_account"] is True
    assert body["status"] == "eligible"
    assert body["eligible"] is True
    assert body["months_consecutive"] == 3


def test_limit_status_unknown_user_404(client):
    resp = client.get("/account/limit-status/NOPE")
    assert resp.status_code == 404


# ── ③ 재학중 신용형성 (인상 스냅샷) ─────────────────────────
def test_credit_profile_snapshot(client):
    resp = client.get(f"/student/credit-profile/{STUDENT_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["months_consecutive"] == 3
    assert body["salary_event_count"] >= 1
    assert "credit_step" in body


# ── 격리 회귀: 둘째 페르소나가 근로자 데이터에 영향 없음 ──────
def test_worker_remittance_path_unaffected(client):
    """근로자 KRW/VND 자동 송금이 유학생 시드 추가 후에도 그대로 동작."""
    resp = client.post("/salary/deposit",
                       json={"user_id": WORKER_ID, "amount_krw": 2_100_000})
    assert resp.status_code == 200
    body = resp.json()
    assert body["remittance"] is not None
    assert len(body["remittance"]["gates"]) == 3
