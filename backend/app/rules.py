"""룰 엔진 3종, 전부 결정적(deterministic). (07 시스템설계 §6)

핵심 원칙: 예측하지 않는다. 환율은 "사용자가 정한 임계조건 충족 시 실행" Rule로만.
사기 판정도 블랙리스트 + 룰 스코어링(LLM 학습 아님).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────────────────────
# 6-1. FX Rule (Gate B), 예측하지 않는다
# ─────────────────────────────────────────────────────────────
@dataclass
class FxDecision:
    decision: str            # TRIGGER_EXECUTE | WAIT | HOLD
    advantage_pct: float
    rate_now: float
    rate_ma: float
    reason: str


def evaluate_fx(
    rate_now: float,
    rate_ma: float,
    threshold_pct: float = 1.0,
    freshness_sec: Optional[float] = None,
) -> FxDecision:
    """advantage_pct = (rate_now − rate_ma) / rate_ma × 100.

    ≥ threshold → TRIGGER_EXECUTE, 아니면 WAIT(6h 재평가).
    데이터 신선도 60초 초과 시 무조건 HOLD.
    """
    if freshness_sec is not None and freshness_sec > 60:
        return FxDecision("HOLD", 0.0, rate_now, rate_ma, "데이터 신선도 60초 초과")

    advantage_pct = (rate_now - rate_ma) / rate_ma * 100.0
    if advantage_pct >= threshold_pct:
        return FxDecision(
            "TRIGGER_EXECUTE", advantage_pct, rate_now, rate_ma,
            f"7일평균 대비 {advantage_pct:.2f}% 유리 → 조건 충족",
        )
    return FxDecision(
        "WAIT", advantage_pct, rate_now, rate_ma,
        f"7일평균 대비 {advantage_pct:.2f}% (임계 {threshold_pct}% 미달) → 대기",
    )


# ─────────────────────────────────────────────────────────────
# 6-2. AML 스크리닝 (Gate C), 의심탐지가 자동실행보다 앞단
# ─────────────────────────────────────────────────────────────
# 스코어 가중치 (§6-2). 블랙리스트는 +100 하드컷.
AML_WEIGHTS = {
    "whitelisted": -40,
    "out_of_mandate": +30,
    "blacklist_hardcut": +100,    # 신분증·비번·OTP·선입금 요구
    "structuring": +50,
    "just_below_threshold_repeat": +30,
    "new_beneficiary": +25,
    "high_amount": +20,           # ≥ 300만
    "late_night": 0,              # 00–05시: STR 기록용 플래그(가산 0), 교대근무 외국인 오탐 방지
}

HIGH_AMOUNT_KRW = 3_000_000
SCORE_HOLD = 40                   # ≥40 보류 + 모국어 질문
SCORE_STR = 70                    # ≥70 STR 후보 큐 + 보류


@dataclass
class AmlDecision:
    decision: str                 # PASS | HOLD | STR_HOLD | BLOCK
    score: int
    flags: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class AmlContext:
    is_whitelisted: bool
    in_mandate_scope: bool
    amount_krw: int
    occurred_at: datetime
    is_new_beneficiary: bool = False
    hit_blacklist: bool = False
    structuring: bool = False
    just_below_threshold_repeat: bool = False


def evaluate_aml(ctx: AmlContext) -> AmlDecision:
    """누적 스코어 → 라우팅. 블랙리스트는 점수와 무관하게 즉시 차단."""
    flags: list[str] = []
    score = 0

    # 블랙리스트 즉시 차단 (하드컷)
    if ctx.hit_blacklist:
        flags.append("blacklist_hardcut")
        return AmlDecision(
            "BLOCK", AML_WEIGHTS["blacklist_hardcut"], flags,
            "블랙리스트(신분증·비번·OTP·선입금 요구) → 즉시 차단",
        )

    if ctx.is_whitelisted:
        score += AML_WEIGHTS["whitelisted"]
        flags.append("whitelisted")
    if not ctx.in_mandate_scope:
        score += AML_WEIGHTS["out_of_mandate"]
        flags.append("out_of_mandate")
    if ctx.structuring:
        score += AML_WEIGHTS["structuring"]
        flags.append("structuring")
    if ctx.just_below_threshold_repeat:
        score += AML_WEIGHTS["just_below_threshold_repeat"]
        flags.append("just_below_threshold_repeat")
    if ctx.is_new_beneficiary:
        score += AML_WEIGHTS["new_beneficiary"]
        flags.append("new_beneficiary")
    if ctx.amount_krw >= HIGH_AMOUNT_KRW:
        score += AML_WEIGHTS["high_amount"]
        flags.append("high_amount")
    if 0 <= ctx.occurred_at.hour < 5:
        score += AML_WEIGHTS["late_night"]    # 가산 0, 플래그로만 기록
        flags.append("late_night")

    score = max(score, 0)

    if score >= SCORE_STR:
        return AmlDecision("STR_HOLD", score, flags,
                           f"score {score} ≥ {SCORE_STR} → STR 후보 큐 + 보류")
    if score >= SCORE_HOLD:
        return AmlDecision("HOLD", score, flags,
                           f"score {score} ≥ {SCORE_HOLD} → 보류 + 모국어 질문")
    return AmlDecision("PASS", score, flags, f"score {score} → 통과")


# ─────────────────────────────────────────────────────────────
# 6-3. 대환 가심사 (2막), 안내·가심사까지, 승인은 JB
# ─────────────────────────────────────────────────────────────
DSR_MAX = 0.40
MULTI_DEBT_MAX = 3
SALARY_MONTHS_MIN = 3
LATE_FEE_SPREAD = 0.03            # 연체가산 = apr + 3%p


@dataclass
class RefiResult:
    eligible: bool
    reasons: list[str]
    annual_saving_krw: int = 0
    new_monthly_krw: int = 0
    new_total_krw: int = 0
    late_fee_apr: float = 0.0
    grade: str = ""
    decision: str = "REFER_TO_JB_ENGINE"   # 승인 아님, JB 회부


def _amortized_monthly(principal: int, apr: float, months: int) -> float:
    """원리금 균등상환 월 납입액."""
    r = apr / 12.0
    if r == 0:
        return principal / months
    return principal * r / (1 - (1 + r) ** (-months))


def prescreen_refi(
    *,
    principal: int,
    current_apr: float,
    jb_apr: float,
    term_months: int,
    visa_remaining_months: int,
    dsr: float,
    multi_debt_count: int,
    salary_months_consecutive: int,
) -> RefiResult:
    """적격 필터 → 절약액·새 월상환·총상환·연체가산 계산.

    승인이 아니라 가심사(REFER_TO_JB_ENGINE). 절약액과 불이익을 동일 비중으로.
    """
    reasons: list[str] = []
    if visa_remaining_months <= term_months:
        reasons.append("비자 잔여기간이 대출 만기보다 짧음")
    if dsr > DSR_MAX:
        reasons.append(f"DSR {dsr:.2f} > {DSR_MAX}")
    if multi_debt_count >= MULTI_DEBT_MAX:
        reasons.append(f"다중채무 {multi_debt_count}건 ≥ {MULTI_DEBT_MAX}")
    if salary_months_consecutive < SALARY_MONTHS_MIN:
        reasons.append(f"급여 연속 {salary_months_consecutive}개월 < {SALARY_MONTHS_MIN}")

    if reasons:
        return RefiResult(eligible=False, reasons=reasons)

    annual_saving = round(principal * (current_apr - jb_apr))
    new_monthly = _amortized_monthly(principal, jb_apr, term_months)
    new_total = new_monthly * term_months

    return RefiResult(
        eligible=True,
        reasons=["적격, 가심사 통과(최종 승인은 JB 심사엔진)"],
        annual_saving_krw=annual_saving,
        new_monthly_krw=round(new_monthly),
        new_total_krw=round(new_total),
        late_fee_apr=round(jb_apr + LATE_FEE_SPREAD, 4),
        grade="가등급 B",
        decision="REFER_TO_JB_ENGINE",
    )
