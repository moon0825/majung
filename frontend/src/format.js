// 표시 포맷터 + 게이트/상태/플래그 라벨 헬퍼 (고객 화면·대시보드 공용)

export const fmtKRW = (n) => (n == null ? "-" : `${Number(n).toLocaleString("ko-KR")}원`);
export const fmtNum = (n) => (n == null ? "-" : Number(n).toLocaleString("ko-KR"));
export const fmtVND = (n) => (n == null ? "-" : `${Math.round(n).toLocaleString("vi-VN")} ₫`);
export const fmtAPR = (r) => (r == null ? "-" : `연 ${(r * 100).toFixed(2)}%`);
export const fmtPct = (x, d = 2) => (x == null ? "-" : `${x >= 0 ? "+" : ""}${Number(x).toFixed(d)}%`);

export const timeHM = (date = new Date()) => {
  const p = (n) => String(n).padStart(2, "0");
  return `${p(date.getHours())}:${p(date.getMinutes())}`;
};

export const timeHMS = (isoOrDate) => {
  try {
    const d = typeof isoOrDate === "string" ? new Date(isoOrDate) : isoOrDate;
    const p = (n) => String(n).padStart(2, "0");
    return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
  } catch {
    return String(isoOrDate ?? "-");
  }
};

// 최종 상태 → 한국어 라벨 + 색상 클래스
export const STATUS_META = {
  executed: { ko: "실행 완료", vi: "Đã thực hiện", cls: "pass" },
  held: { ko: "보류", vi: "Tạm giữ", cls: "hold" },
  str_hold: { ko: "보류 + STR", vi: "Tạm giữ + STR", cls: "hold" },
  blocked: { ko: "차단", vi: "Đã chặn", cls: "block" },
  rejected: { ko: "거절", vi: "Từ chối", cls: "block" },
};
export const statusMeta = (s) => STATUS_META[s] || { ko: s || "-", vi: "", cls: "na" };

// AML 플래그 → 한국어
export const FLAG_KO = {
  whitelisted: "화이트리스트",
  out_of_mandate: "위임 범위 밖",
  new_beneficiary: "신규 수취인",
  high_amount: "고액(300만 원 이상)",
  late_night: "심야(00~05시)",
  structuring: "분할거래 의심",
  just_below_threshold_repeat: "임계치 직하 반복",
  blacklist_hardcut: "블랙리스트 즉시 차단",
};
export const flagKo = (f) => FLAG_KO[f] || f;

export const GATE_NAME = { A: "위임장", B: "Rule·FX", C: "AML" };

// 게이트 한 칸의 표시 텍스트/색 (outcome.gates 기반)
export function gateCell(outcome, letter) {
  const g = outcome?.gates?.find((x) => x.gate === letter);
  if (!g) return { text: "-", cls: "na" };
  if (g.passed) return { text: "PASS", cls: "pass" };
  if (g.detail?.skipped) return { text: "회부", cls: "hold" };
  const decision = g.detail?.decision || g.detail?.fx_decision?.decision;
  if (decision === "BLOCK") return { text: "BLOCK", cls: "block" };
  if (decision === "STR_HOLD") return { text: "STR", cls: "hold" };
  if (decision === "HOLD" || decision === "WAIT") return { text: decision, cls: "hold" };
  return { text: "STOP", cls: "block" };
}

// 게이트 C(AML) 디테일에서 score / flags 추출
export function amlOf(outcome) {
  const g = outcome?.gates?.find((x) => x.gate === "C");
  return { score: g?.detail?.score ?? null, flags: g?.detail?.flags ?? [] };
}

// 게이트 B 디테일에서 FX 추출
export function fxOf(outcome) {
  const g = outcome?.gates?.find((x) => x.gate === "B");
  return {
    rateNow: g?.detail?.fx?.rate_now ?? null,
    rateMa: g?.detail?.fx?.rate_ma ?? null,
    advantagePct: g?.detail?.fx_decision?.advantage_pct ?? null,
  };
}
