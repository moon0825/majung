"""데모 데이터 시드, `python -m app.seed` 로 DB 생성·초기화.

데모 수치 재현 (07 §6):
- FX: 7일평균 18.12 vs 현재 18.45 = +1.82% → 조건 충족
- 대환: 사채 1,500만 연 30% → JB 연 13.59% = 연 246만원 절약
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from .db import DB_PATH, get_conn, init_schema

USER_ID = "USR-VN-1029"

# 7일 평균이 정확히 18.12가 되도록 구성 (합계 126.84 / 7)
_FX_HISTORY = [18.00, 18.10, 18.05, 18.20, 18.18, 18.14, 18.17]
_FX_NOW = 18.45

# ── v2 유학생 세그먼트(둘째 페르소나) — 추가만, 기존 근로자 데이터 무수정 ──
# 같은 엔진(3중 게이트)·두 입구. 등록금 외화 송금은 KRW/CNY 페어로 동일 경로 재사용.
STUDENT_ID = "USR-CN-2050"
STUDENT_MANDATE_ID = "MND-2026-CN01"
STUDENT_BNF_ID = "CN-UNIV-01"           # 대학 등록금 수취인(화이트리스트)
STUDENT_TUITION_KRW = 3_500_000         # 한 학기 등록금(한도 4백만 내)

# KRW/CNY 7일 평균이 정확히 0.5200(합계 3.64 / 7), 현재 0.5296 = +1.846% → 게이트 B 통과
_FX_CNY_HISTORY = [0.5180, 0.5220, 0.5190, 0.5210, 0.5200, 0.5205, 0.5195]
_FX_CNY_NOW = 0.5296


def _student_mandate_json() -> str:
    return json.dumps({
        "mandate_id": STUDENT_MANDATE_ID,
        "user_id": STUDENT_ID,
        "mandate_type": "remittance",
        "language": "zh",
        "beneficiary_whitelist": [
            {"bnf_id": STUDENT_BNF_ID, "name": "전북대학교 등록금 수납계좌",
             "relation": "university", "bank": "JB은행", "account_masked": "****2050",
             "added_at": "2026-03-01T09:00:00Z"},
        ],
        "limits": {"limit_per_tx_krw": 4_000_000, "limit_monthly_krw": 4_000_000,
                   "currency_target": "CNY"},
        "trigger": {"type": "salary_in", "min_salary_krw": 500_000},
        "fx_condition": {"type": "better_than_ma", "window_days": 7,
                         "threshold_pct": 1.0, "direction": "favorable"},
        "on_exception": "hold_and_ask",
        "ask_timeout_min": 720,
        "valid_until": "2028-12-31T23:59:59Z",
        "esign": {"signed_at": "2026-03-02T08:00:00Z", "method": "biometric_or_pin_mock",
                  "esign_hash": "sha256:cn2050aabb01", "reconfirmed_in_language": True},
        "revocation": {"revocable": True, "revoked": False, "revoked_at": None},
        "notification": {"per_execution": True, "channel": "in_app_push", "language": "zh"},
        "audit_log_ref": "LOG-MND-CN01",
    }, ensure_ascii=False)


def _seed_student(conn) -> None:
    """v2 둘째 페르소나(유학생 Wang Wei, D-2). 전부 user-scoped 추가 → 기존 테스트 무영향."""
    m = json.loads(_student_mandate_json())
    conn.execute(
        "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
        (STUDENT_ID, "Wang Wei", "China", "D-2", "2028-12-31", "zh", "active"),
    )
    # 한도계좌(is_limited_account=1), 연속급여 3개월 → 한도해제 코치 'eligible'
    conn.execute(
        "INSERT INTO accounts(account_id, user_id, balance_krw, is_limited_account, "
        "salary_months_consecutive) VALUES (?,?,?,?,?)",
        ("ACC-2050", STUDENT_ID, 1_200_000, 1, 3),
    )
    base = datetime.now()
    for i in range(3):                  # 최근 3개월 급여(신용형성 스냅샷 프록시)
        d = (base - timedelta(days=30 * i)).isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO salary_events(user_id, amount_krw, deposited_at) VALUES (?,?,?)",
            (STUDENT_ID, 1_200_000, d),
        )

    # FX, KRW/CNY (별도 페어 → 기존 KRW/VND 무영향)
    today = base.date()
    for i, rate in enumerate(reversed(_FX_CNY_HISTORY), start=1):
        d = (today - timedelta(days=i)).isoformat()
        conn.execute("INSERT INTO fx_rates VALUES (?,?,?)", ("KRW/CNY", d, rate))
    conn.execute("INSERT INTO fx_rates VALUES (?,?,?)", ("KRW/CNY", today.isoformat(), _FX_CNY_NOW))

    # active 등록금 위임장
    conn.execute(
        "INSERT INTO mandates(mandate_id, user_id, json_blob, status, valid_until, "
        "esign_hash, revoked) VALUES (?,?,?,?,?,?,?)",
        (STUDENT_MANDATE_ID, STUDENT_ID, _student_mandate_json(), "active",
         m["valid_until"], m["esign"]["esign_hash"], 0),
    )
    # 대학 등록금 수취인(화이트리스트)
    conn.execute(
        "INSERT INTO beneficiaries(bnf_id, user_id, name, bank, account_masked, "
        "is_whitelisted, first_seen) VALUES (?,?,?,?,?,?,?)",
        (STUDENT_BNF_ID, STUDENT_ID, "전북대학교 등록금 수납계좌", "JB은행", "****2050", 1,
         "2026-03-01T09:00:00Z"),
    )
    # ④ 졸업전환 가심사 재사용 준비용 소액 채무(원화 절약 헤드라인은 UI에서 미노출)
    conn.execute(
        "INSERT INTO loans_external(user_id, principal, apr, lender, remaining_months) "
        "VALUES (?,?,?,?,?)",
        (STUDENT_ID, 8_000_000, 0.24, "유학생 카드론", 24),
    )


def _mandate_json() -> str:
    return json.dumps({
        "mandate_id": "MND-2026-0001",
        "user_id": USER_ID,
        "mandate_type": "remittance",
        "language": "vi",
        "beneficiary_whitelist": [
            {"bnf_id": "VN-BNF-01", "name": "Nguyen Thi Lan", "relation": "mother",
             "bank": "Vietcombank", "account_masked": "****8821",
             "added_at": "2026-06-01T10:00:00Z"},
        ],
        "limits": {"limit_per_tx_krw": 2000000, "limit_monthly_krw": 2000000,
                   "currency_target": "VND"},
        "trigger": {"type": "salary_in", "min_salary_krw": 500000},
        "fx_condition": {"type": "better_than_ma", "window_days": 7,
                         "threshold_pct": 1.0, "direction": "favorable"},
        "on_exception": "hold_and_ask",
        "ask_timeout_min": 720,
        "valid_until": "2026-12-31T23:59:59Z",
        "esign": {"signed_at": "2026-06-06T08:00:00Z", "method": "biometric_or_pin_mock",
                  "esign_hash": "sha256:ab12cd34ef56", "reconfirmed_in_language": True},
        "revocation": {"revocable": True, "revoked": False, "revoked_at": None},
        "notification": {"per_execution": True, "channel": "in_app_push", "language": "vi"},
        "audit_log_ref": "LOG-MND-0001",
    }, ensure_ascii=False)


def seed() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = get_conn()
    init_schema(conn)

    conn.execute(
        "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
        (USER_ID, "Tran Van Minh", "Vietnam", "E-9", "2029-12-31", "vi", "active"),
    )
    conn.execute(
        "INSERT INTO accounts(account_id, user_id, balance_krw, is_limited_account, "
        "salary_months_consecutive) VALUES (?,?,?,?,?)",
        ("ACC-1029", USER_ID, 2_350_000, 1, 4),
    )
    conn.execute(
        "INSERT INTO salary_events(user_id, amount_krw, deposited_at) VALUES (?,?,?)",
        (USER_ID, 2_100_000, datetime.now().isoformat(timespec="seconds")),
    )

    # FX, KRW/VND
    base = datetime.now().date()
    for i, rate in enumerate(reversed(_FX_HISTORY), start=1):
        d = (base - timedelta(days=i)).isoformat()
        conn.execute("INSERT INTO fx_rates VALUES (?,?,?)", ("KRW/VND", d, rate))
    conn.execute("INSERT INTO fx_rates VALUES (?,?,?)", ("KRW/VND", base.isoformat(), _FX_NOW))

    # 위임장
    m = json.loads(_mandate_json())
    conn.execute(
        "INSERT INTO mandates(mandate_id, user_id, json_blob, status, valid_until, "
        "esign_hash, revoked) VALUES (?,?,?,?,?,?,?)",
        ("MND-2026-0001", USER_ID, _mandate_json(), "active", m["valid_until"],
         m["esign"]["esign_hash"], 0),
    )

    # 수취인: 화이트리스트(어머니), 신규 의심(미등록), 사기(메모)
    conn.executemany(
        "INSERT INTO beneficiaries(bnf_id, user_id, name, bank, account_masked, "
        "is_whitelisted, first_seen) VALUES (?,?,?,?,?,?,?)",
        [
            ("VN-BNF-01", USER_ID, "Nguyen Thi Lan", "Vietcombank", "****8821", 1,
             "2026-06-01T10:00:00Z"),
            ("VN-BNF-99", USER_ID, "Unknown Payee", "Unknown", "****0000", 0, None),
            ("SCAM-OTP-01", USER_ID, "OTP 신분증 선입금 요구", "Unknown", "****1111", 0, None),
        ],
    )

    # 사채 / 대환상품 / 블랙리스트
    conn.execute(
        "INSERT INTO loans_external(user_id, principal, apr, lender, remaining_months) "
        "VALUES (?,?,?,?,?)",
        (USER_ID, 15_000_000, 0.30, "브로커사채", 36),
    )
    conn.execute(
        "INSERT INTO refi_products(name, apr, max_term_months) VALUES (?,?,?)",
        ("JB 외국인 대환", 0.1359, 36),
    )
    conn.executemany(
        "INSERT INTO blacklist_patterns(pattern_type, keyword) VALUES (?,?)",
        [("loan_scam", "OTP"), ("loan_scam", "신분증"), ("loan_scam", "선입금"),
         ("phishing", "비밀번호"), ("phishing", "비번")],
    )

    # ── v2 유학생 세그먼트(둘째 페르소나) 추가 ──
    _seed_student(conn)

    conn.commit()
    conn.close()
    print(f"[seed] DB 생성 완료: {DB_PATH}")
    print(f"[seed] 근로자={USER_ID} / 위임장=MND-2026-0001 / FX=KRW/VND")
    print(f"[seed] 유학생={STUDENT_ID} / 위임장={STUDENT_MANDATE_ID} / FX=KRW/CNY")


if __name__ == "__main__":
    seed()
