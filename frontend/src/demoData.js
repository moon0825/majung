// 시드(app/seed.py) 기준 데모 상수 + 오프라인 미리보기용 목 데이터.
// 백엔드가 살아 있으면 목은 절대 쓰지 않는다(헬스체크로 분기).

export const USER_ID = "USR-VN-1029";
export const USER_NAME = "Tran Van Minh";
export const ACCOUNT_ID = "ACC-1029";
export const SEED_BALANCE = 2_350_000;
export const SEED_MANDATE_ID = "MND-2026-0001";
export const SEED_ESIGN_HASH = "sha256:ab12cd34ef56";

export const SALARY_KRW = 2_100_000;
export const REMIT_KRW = 2_000_000;

export const MOTHER = {
  id: "VN-BNF-01",
  nameVi: "Nguyễn Thị Lan",
  label: "Nguyễn Thị Lan (Mẹ / 어머니)",
  bank: "Vietcombank",
  masked: "****8821",
};
export const HOLD_BNF = { id: "VN-BNF-99", label: "Unknown Payee (신규)", amountKrw: 4_800_000 };
export const SCAM_BNF = { id: "SCAM-OTP-01", label: "OTP 요구 수취인", amountKrw: 3_000_000 };

export const FX_SEED = { now: 18.45, ma: 18.12, advantagePct: 1.82 };

// 데모 발화(촬영 고정 스크립트), llm.py 힌트("gửi"/"vay"/"hủy")와 일치
export const SCRIPT_REMIT = "Khi có lương, nếu tỷ giá tốt, gửi 2 triệu KRW cho mẹ tôi nhé.";
export const SCRIPT_REFI = "Tôi muốn giảm lãi khoản vay của tôi.";
export const SCRIPT_REVOKE = "Hủy ủy quyền.";

// 새벽 02:40 (오늘 날짜), AML late_night 플래그 재현
export function lateNightISO() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T02:40:00`;
}

// ── 오프라인 미리보기 목 (백엔드 응답 스키마 그대로 재현) ──
export const MOCK = {
  executed: () => ({
    status: "executed",
    message_ko: "환율이 좋아 어머니께 자동 송금했어요.",
    message_local: "Đã tự động gửi tiền cho mẹ vì tỷ giá tốt.",
    tx_id: "TX-OFFLINE001",
    gates: [
      { gate: "A", label: "위임장 검증 (Mandate Validation)", passed: true,
        detail: { valid: true, in_mandate_scope: true } },
      { gate: "B", label: "Rule 한도·조건 (Rule Limits)", passed: true,
        detail: {
          limits: { within_limit: true, remaining_monthly_krw: 2_000_000 },
          fx: { rate_now: FX_SEED.now, rate_ma: FX_SEED.ma },
          fx_decision: { decision: "TRIGGER_EXECUTE", advantage_pct: FX_SEED.advantagePct },
        } },
      { gate: "C", label: "수취인 화이트리스트 + AML 스크리닝", passed: true,
        detail: { score: 0, flags: ["whitelisted"], decision: "PASS" } },
    ],
  }),

  strHold: () => ({
    status: "str_hold",
    message_ko: "의심 거래로 보류하고 검토 대기열에 넣었어요.",
    message_local: "Giao dịch nghi ngờ, đã tạm giữ và đưa vào hàng đợi kiểm tra.",
    tx_id: null,
    gates: [
      { gate: "A", label: "위임장 검증 (Mandate Validation)", passed: true,
        detail: { valid: true, in_mandate_scope: false } },
      { gate: "B", label: "Rule 한도·조건 (Rule Limits)", passed: false,
        detail: { skipped: "위임 범위 밖: on_exception=hold_and_ask, AML로 회부" } },
      { gate: "C", label: "수취인 화이트리스트 + AML 스크리닝", passed: false,
        detail: { score: 75, flags: ["out_of_mandate", "new_beneficiary", "high_amount", "late_night"],
                  decision: "STR_HOLD" } },
    ],
  }),

  blocked: () => ({
    status: "blocked",
    message_ko: "비밀번호와 OTP는 절대 알려주지 마세요. 거래를 차단했습니다.",
    message_local: "Đừng bao giờ cung cấp mật khẩu/OTP. Đã chặn.",
    tx_id: null,
    gates: [
      { gate: "A", label: "위임장 검증 (Mandate Validation)", passed: true,
        detail: { valid: true, in_mandate_scope: false } },
      { gate: "B", label: "Rule 한도·조건 (Rule Limits)", passed: false,
        detail: { skipped: "위임 범위 밖: on_exception=hold_and_ask, AML로 회부" } },
      { gate: "C", label: "수취인 화이트리스트 + AML 스크리닝", passed: false,
        detail: { score: 100, flags: ["blacklist_hardcut"], decision: "BLOCK" } },
    ],
  }),

  refi: () => ({
    eligible: true,
    reasons: ["적격: 가심사 통과 (최종 승인은 JB 심사엔진)"],
    annual_saving_krw: 2_461_500,
    new_monthly_krw: 509_723,
    new_total_krw: 18_350_028,
    late_fee_apr: 0.1659,
    grade: "가등급 B",
    decision: "REFER_TO_JB_ENGINE",
    lender: "브로커사채",
    current_apr: 0.30,
    jb_product: "JB 외국인 대환",
    jb_apr: 0.1359,
    term_months: 36,
  }),
};

// ── 사업가치 콘솔(관리자 전용) 표시값. 거시 수치는 자체 추정, 1인당 절약은 치트시트 확정. ──
// 세션 행동(traces)과 무관한 정적 거시값이라 시연 중에도 일관되게 유지된다.
export const BIZ = {
  refiConversionRate: 0.07,
  refiBalanceKrw: 50_400_000_000,
  annualInterestKrw: 4_812_150_000,
  perCapitaSavingKrw: 2_461_500,
  cumulativeBorrowers: 240_000,
  marketSharePct: 72,
  loanSharkApr: 0.30,
  jbRefiApr: 0.1359,
  funnel: [
    { stage: "가심사 적격", pct: 100, locked: false },
    { stage: "가심사 안내", pct: 92, locked: false },
    { stage: "JB 회부", pct: 41, locked: false },
    { stage: "승인 (JB 심사엔진)", pct: 18, locked: true },
    { stage: "실행", pct: 7, locked: false },
  ],
};
