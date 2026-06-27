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

    conn.commit()
    conn.close()
    print(f"[seed] DB 생성 완료: {DB_PATH}")
    print(f"[seed] 사용자={USER_ID} / 위임장=MND-2026-0001 / FX=KRW/VND")


if __name__ == "__main__":
    seed()
