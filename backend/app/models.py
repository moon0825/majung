"""Pydantic 스키마, 위임장(Mandate) 등. (07 시스템설계 §3 확정본)

전금법 거래지시 요건: 전자서명(esign) + 건별 통지(notify) + 무조건 철회권(revoke) 3종 내장.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Beneficiary(BaseModel):
    bnf_id: str
    name: str
    relation: Optional[str] = None
    bank: Optional[str] = None
    account_masked: Optional[str] = None
    added_at: Optional[str] = None


class Limits(BaseModel):
    limit_per_tx_krw: int
    limit_monthly_krw: int
    currency_target: str = "VND"


class Trigger(BaseModel):
    type: Literal["salary_in", "manual"] = "salary_in"
    min_salary_krw: int = 500000


class FxCondition(BaseModel):
    type: Literal["better_than_ma"] = "better_than_ma"
    window_days: int = 7
    threshold_pct: float = 1.0          # 7일평균 대비 ≥1% 유리
    direction: Literal["favorable"] = "favorable"


class ESign(BaseModel):
    """① 전자서명, 위임 내용 해시로 변조 방지."""
    signed_at: str
    method: str = "biometric_or_pin_mock"
    esign_hash: str
    reconfirmed_in_language: bool = True  # 모국어 재확인(브라보 리뷰 해소)


class Revocation(BaseModel):
    """③ 무조건 철회권."""
    revocable: bool = True
    revoked: bool = False
    revoked_at: Optional[str] = None


class Notification(BaseModel):
    """② 건별 통지."""
    per_execution: bool = True
    channel: str = "in_app_push"
    language: str = "vi"


class Mandate(BaseModel):
    """위임장, §3 확정 스키마."""
    mandate_id: str
    user_id: str
    mandate_type: Literal["remittance", "loan_refi"] = "remittance"
    language: str = "vi"

    beneficiary_whitelist: list[Beneficiary] = Field(default_factory=list)
    limits: Limits
    trigger: Trigger = Field(default_factory=Trigger)
    fx_condition: FxCondition = Field(default_factory=FxCondition)

    on_exception: Literal["hold_and_ask"] = "hold_and_ask"
    ask_timeout_min: int = 720           # 무응답 시 자동 취소(실행 안 함)

    valid_until: str
    esign: ESign
    revocation: Revocation = Field(default_factory=Revocation)
    notification: Notification = Field(default_factory=Notification)
    audit_log_ref: Optional[str] = None


class RemittanceRequest(BaseModel):
    mandate_id: str
    bnf_id: str
    amount_krw: int
    occurred_at: Optional[str] = None    # ISO datetime (심야 판정용); 없으면 now


class RefiPrescreenRequest(BaseModel):
    user_id: str


# ── 위임장 발급·서명 요청 ──────────────────────────────────────
class MandateIssueRequest(BaseModel):
    """POST /mandate/issue 요청, 초안으로 pending_sign 위임장 생성."""
    user_id: str
    draft: dict                          # 위임장 필드 (mandate_id 미포함 시 자동 생성)


# ── 급여 입금 트리거 요청 ─────────────────────────────────────
class SalaryDepositRequest(BaseModel):
    """POST /salary/deposit 요청, 급여 감지 후 자동 송금 트리거 시뮬레이션."""
    user_id: str
    amount_krw: int
