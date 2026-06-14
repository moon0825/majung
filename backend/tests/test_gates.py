"""게이트·룰 데모 수치 재현 검증 (07 §6).

실행: cd backend && pytest
"""
from datetime import datetime

from app import rules


def test_fx_advantage_reproduces_1_82pct():
    d = rules.evaluate_fx(rate_now=18.45, rate_ma=18.12, threshold_pct=1.0)
    assert d.decision == "TRIGGER_EXECUTE"
    assert round(d.advantage_pct, 2) == 1.82


def test_fx_below_threshold_waits():
    d = rules.evaluate_fx(rate_now=18.13, rate_ma=18.12, threshold_pct=1.0)
    assert d.decision == "WAIT"


def test_fx_stale_data_holds():
    d = rules.evaluate_fx(rate_now=18.45, rate_ma=18.12, freshness_sec=120)
    assert d.decision == "HOLD"


def test_aml_blacklist_hardcut_blocks():
    ctx = rules.AmlContext(
        is_whitelisted=False, in_mandate_scope=True, amount_krw=1_000_000,
        occurred_at=datetime(2026, 6, 6, 14, 0), hit_blacklist=True,
    )
    d = rules.evaluate_aml(ctx)
    assert d.decision == "BLOCK"


def test_aml_out_of_mandate_new_high_amount_scores_75_and_routes_to_str():
    # 위임밖(+30) + 신규(+25) + 고액(+20) = 75. 심야는 플래그(가산 0) → STR_HOLD
    ctx = rules.AmlContext(
        is_whitelisted=False, in_mandate_scope=False, amount_krw=4_800_000,
        occurred_at=datetime(2026, 6, 7, 2, 40), is_new_beneficiary=True,
    )
    d = rules.evaluate_aml(ctx)
    assert d.score == 75                      # 데모 통일값
    assert d.decision == "STR_HOLD"
    assert "late_night" in d.flags            # 새벽은 표시되되 점수 가산 없음


def test_aml_whitelisted_in_scope_passes():
    ctx = rules.AmlContext(
        is_whitelisted=True, in_mandate_scope=True, amount_krw=2_000_000,
        occurred_at=datetime(2026, 6, 6, 9, 0),
    )
    d = rules.evaluate_aml(ctx)
    assert d.decision == "PASS"


def test_refi_saving_reproduces_246man():
    r = rules.prescreen_refi(
        principal=15_000_000, current_apr=0.30, jb_apr=0.1359, term_months=36,
        visa_remaining_months=48, dsr=0.32, multi_debt_count=1,
        salary_months_consecutive=4,
    )
    assert r.eligible
    # 1500만 × (30% − 13.59%) = 246.15만
    assert abs(r.annual_saving_krw - 2_461_500) < 1000
    assert 500_000 < r.new_monthly_krw < 520_000     # ~51.1만


def test_refi_visa_too_short_rejected():
    r = rules.prescreen_refi(
        principal=15_000_000, current_apr=0.30, jb_apr=0.1359, term_months=36,
        visa_remaining_months=12, dsr=0.32, multi_debt_count=1,
        salary_months_consecutive=4,
    )
    assert not r.eligible
