"""계좌 활성화 레이어 — 한도계좌 → 정식계좌 승급 판정 (결정적).

마중 v2 서사: JB가 외국인 금융 인프라(가계좌·한도계좌)를 이미 깔았고,
마중은 그 위에서 "언제 한도해제가 가능한가"를 코치하는 활성화 레이어다.

제1원칙 동일: 예측하지 않는다. 승급 가능 여부는 결정적 규칙(연속급여 N개월)으로만.
이 모듈은 rules.py(송금 게이트) 밖의 신규 판정 로직이며, 송금 실행 경로를 건드리지 않는다.
자금 이동이 전혀 없는 read-only 판정 — 안내·코치 용도.
"""
from __future__ import annotations

from dataclasses import dataclass

# 한도계좌 → 정식계좌 승급 기준 (치트시트 확정값)
LIMIT_RELEASE_MIN_MONTHS = 3          # 연속 급여 입금 3개월
LIMIT_RELEASE_MIN_SALARY_KRW = 500_000  # 월 급여 인정 하한


@dataclass
class LimitReleaseResult:
    status: str                # full_account | eligible | in_progress
    eligible: bool             # 지금 한도해제 신청 가능 여부
    months_consecutive: int
    min_months: int
    remaining_months: int
    min_salary_krw: int
    message_ko: str
    message_local: str         # 유학생 모국어(중국어)


def evaluate_limit_release(
    *,
    is_limited_account: bool,
    salary_months_consecutive: int,
    min_months: int = LIMIT_RELEASE_MIN_MONTHS,
    min_salary_krw: int = LIMIT_RELEASE_MIN_SALARY_KRW,
) -> LimitReleaseResult:
    """한도계좌 승급 판정.

    - 이미 정식계좌면 status=full_account (코치 불필요).
    - 연속 급여 ≥ min_months → eligible (한도해제 신청 안내).
    - 미달이면 in_progress + 남은 개월 안내.
    """
    months = max(0, int(salary_months_consecutive))

    if not is_limited_account:
        return LimitReleaseResult(
            status="full_account",
            eligible=False,
            months_consecutive=months,
            min_months=min_months,
            remaining_months=0,
            min_salary_krw=min_salary_krw,
            message_ko="이미 정식계좌입니다. 한도 없이 전체 금융 서비스를 이용할 수 있어요.",
            message_local="您已是正式账户，可无限额使用全部金融服务。",
        )

    remaining = max(0, min_months - months)
    if remaining == 0:
        return LimitReleaseResult(
            status="eligible",
            eligible=True,
            months_consecutive=months,
            min_months=min_months,
            remaining_months=0,
            min_salary_krw=min_salary_krw,
            message_ko=(
                f"급여가 {months}개월 연속 입금되어 한도계좌 해제 조건을 충족했어요. "
                "지금 정식계좌로 전환을 신청할 수 있습니다."
            ),
            message_local=(
                f"工资已连续入账 {months} 个月，已满足限额账户解除条件。"
                "现在即可申请转为正式账户。"
            ),
        )

    return LimitReleaseResult(
        status="in_progress",
        eligible=False,
        months_consecutive=months,
        min_months=min_months,
        remaining_months=remaining,
        min_salary_krw=min_salary_krw,
        message_ko=(
            f"급여 연속 입금 {months}/{min_months}개월. "
            f"{remaining}개월 더 쌓이면 한도계좌를 해제할 수 있어요."
        ),
        message_local=(
            f"工资连续入账 {months}/{min_months} 个月。"
            f"再积累 {remaining} 个月即可解除限额账户。"
        ),
    )
