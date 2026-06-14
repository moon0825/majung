// 백엔드 호출 단일 창구. vite proxy: /api → :8000.
// 원칙: 절대 throw 하지 않는다, 데모(영상 촬영) 중 화면이 죽으면 안 된다.
// 모든 함수는 { ok, status, data, error } 를 반환한다.
const BASE = "/api";

async function call(path, { method = "GET", body, timeoutMs = 8000 } = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(BASE + path, {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    });
    let data = null;
    try { data = await res.json(); } catch { /* 본문 없는 응답 허용 */ }
    if (!res.ok) {
      const msg = (data && (data.detail || data.error || data.message)) || `HTTP ${res.status}`;
      return { ok: false, status: res.status, data, error: String(msg) };
    }
    return { ok: true, status: res.status, data, error: null };
  } catch {
    return { ok: false, status: 0, data: null, error: "백엔드(8000) 연결 실패" };
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  health: () => call("/health", { timeoutMs: 2500 }),

  // LLM은 의도 파싱만, 실행 결정은 게이트가
  chat: (text, userId) =>
    call("/chat", { method: "POST", body: { text, user_id: userId } }),

  // 신규 5종 (백엔드 동시 보강 중, 실패 시 호출부에서 시드 값으로 폴백)
  issueMandate: (payload) =>
    call("/mandate/issue", { method: "POST", body: payload }),
  signMandate: (mandateId, payload = {}) =>
    call(`/mandate/${mandateId}/sign`, { method: "POST", body: payload }),
  salaryDeposit: (userId, amountKrw) =>
    call("/salary/deposit", { method: "POST", body: { user_id: userId, amount_krw: amountKrw } }),
  notifications: (userId) => call(`/notifications/${userId}`, { timeoutMs: 4000 }),

  // 기존 엔드포인트
  executeRemittance: ({ mandateId, bnfId, amountKrw, occurredAt }) =>
    call("/remittance/execute", {
      method: "POST",
      body: {
        mandate_id: mandateId,
        bnf_id: bnfId,
        amount_krw: amountKrw,
        occurred_at: occurredAt ?? null,
      },
    }),
  fx: (base = "KRW", quote = "VND") => call(`/fx/${base}/${quote}`),
  refiPrescreen: (userId) =>
    call("/refi/prescreen", { method: "POST", body: { user_id: userId } }),
  refiRefer: (userId, draft) =>
    call("/refi/refer", { method: "POST", body: { user_id: userId, refi_draft: draft } }),
  revokeMandate: (mandateId) =>
    call(`/mandate/${mandateId}/revoke`, { method: "POST" }),
  audit: (userId) => call(`/audit/${userId}`),
  strQueue: () => call("/str-queue"),
};

// /salary/deposit 응답이 자동집행 결과(gates)를 어디에 품고 있어도 찾아낸다.
// (백엔드 보강 형태가 미확정, 어떤 키로 와도 흡수)
export function extractOutcome(data) {
  if (!data || typeof data !== "object") return null;
  if (Array.isArray(data.gates) && data.status) return data;
  for (const key of ["remittance", "outcome", "result", "execution", "auto_remit"]) {
    const v = data[key];
    if (v && typeof v === "object" && Array.isArray(v.gates) && v.status) return v;
  }
  return null;
}
