import { useCallback, useEffect, useRef, useState } from "react";
import { api, extractOutcome } from "./api.js";
import * as D from "./demoData.js";
import PhoneFrame from "./components/PhoneFrame.jsx";
import CustomerChat from "./components/CustomerChat.jsx";
import ControlPanel from "./components/ControlPanel.jsx";
import AdminDashboard from "./components/AdminDashboard.jsx";
import StudentView from "./components/StudentView.jsx";

// ───────────────────────────────────────────────────────────────
// 아키텍처 제1원칙: 송금 실행 경로에서 LLM을 배제하고, 한도와 화이트리스트로
// 최대 손실을 사전에 제한한다. 이 UI도 동일하게, 카드와 버튼은 백엔드의
// 3중 게이트 판정 "결과"를 보여줄 뿐, 실행 여부를 프론트가 결정하지 않는다.
// ───────────────────────────────────────────────────────────────

let seq = 0;
const nid = () => `f${++seq}`;

// 연출용 최소 대기: 백엔드가 빨라도 카드가 즉시 튀지 않고
// "감지 → 판정 → 실행" 순서가 눈에 보이도록 일정 간격을 보장한다.
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const paced = async (promise, ms) => (await Promise.all([promise, wait(ms)]))[0];

const GREETING = () => [
  { id: nid(), kind: "bot",
    vi: "Xin chào anh Minh! Tôi là Majung, trợ lý ngân hàng ủy quyền của anh.",
    ko: "안녕하세요, 민 님. 위임형 뱅킹 에이전트 '마중'입니다." },
  { id: nid(), kind: "bot",
    vi: "Tôi biết anh đang gánh khoản vay 1.500 만원, lãi 30%/năm từ trước khi sang Hàn. Tôi giúp anh gửi tiền an toàn về nhà và từng bước giảm lãi khoản vay đó.",
    ko: "입국 전 떠안으신 1,500만원·연 30% 사채를 알고 있어요. 안전한 송금과, 그 사채를 한 걸음씩 줄이는 일을 함께 도와드릴게요." },
  { id: nid(), kind: "bot",
    vi: "Anh cần gì? Có thể nói bằng tiếng Việt.",
    ko: "무엇을 도와드릴까요? 베트남어로 말씀하셔도 됩니다." },
];

// llm.py 폴백 미러: /chat 호출이 실패해도 채팅 데모는 진행된다
const HINTS = {
  revoke: ["취소", "철회", "그만", "hủy", "dừng"],
  refi: ["대출", "사채", "대환", "빚", "vay", "nợ", "lãi"],
  remit: ["보내", "송금", "gửi", "chuyển", "remit"],
};
function localIntent(text) {
  const t = text.toLowerCase();
  for (const intent of ["revoke", "refi", "remit"]) {
    if (HINTS[intent].some((h) => t.includes(h))) return intent;
  }
  return "unknown";
}

export default function App() {
  const [tab, setTab] = useState("customer");
  const [healthy, setHealthy] = useState(false);
  const [busy, setBusy] = useState(false);
  const [feed, setFeed] = useState(GREETING);
  const [traces, setTraces] = useState([]);
  const [balance, setBalance] = useState(D.SEED_BALANCE);
  const [mandate, setMandate] = useState({ id: D.SEED_MANDATE_ID, status: "active" });
  // 촬영 모드: 컨트롤 패널을 화면 밖으로 이동, 진행자는 숫자 단축키로 조작
  const [film, setFilm] = useState(false);

  const healthRef = useRef(false);
  const mandateRef = useRef(mandate);
  mandateRef.current = mandate;
  // busy 상태의 동기 거울: 같은 프레임 안의 연속 클릭(상태 반영 전)도 차단한다
  const busyRef = useRef(false);
  const lock = () => {
    if (busyRef.current) return false;
    busyRef.current = true;
    setBusy(true);
    return true;
  };
  const unlock = () => {
    busyRef.current = false;
    setBusy(false);
  };

  // ── 헬스체크 (8초 주기): 오프라인이면 목 데이터로 레이아웃 미리보기 ──
  useEffect(() => {
    let alive = true;
    const check = async () => {
      const r = await api.health();
      if (!alive) return;
      healthRef.current = r.ok;
      setHealthy(r.ok);
    };
    check();
    const t = setInterval(check, 8000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  // ── 피드 헬퍼 ──
  const push = useCallback((item) => {
    const it = { id: nid(), ts: new Date(), ...item };
    setFeed((f) => [...f, it]);
    return it.id;
  }, []);
  const patch = useCallback((id, p) => {
    setFeed((f) => f.map((it) => (it.id === id ? { ...it, ...p } : it)));
  }, []);
  const pushError = useCallback((msg) => {
    push({ kind: "error", message: msg || "요청 실패" });
  }, [push]);

  const addTrace = useCallback((outcome, meta) => {
    setTraces((t) => [
      { ts: new Date(), bnf: meta.bnfLabel, amountKrw: meta.amountKrw, outcome },
      ...t,
    ]);
  }, []);

  const finishOutcome = useCallback((outcome, meta) => {
    push({ kind: "outcome", outcome, bnfLabel: meta.bnfLabel, amountKrw: meta.amountKrw });
    if (outcome.status === "executed") setBalance((b) => b - meta.amountKrw);
    addTrace(outcome, meta);
  }, [push, addTrace]);

  // ── 알림 폴링 (신규 /notifications/{user_id}, 미구현이면 자동 비활성) ──
  const notifOk = useRef(true);
  const seenNotifs = useRef(null);
  const suppressUntil = useRef(0);
  const suppressNotifs = () => { suppressUntil.current = Date.now() + 6000; };
  useEffect(() => {
    const keyOf = (n) => n?.id ?? n?.notif_id ?? n?.log_id ?? JSON.stringify(n);
    const t = setInterval(async () => {
      if (!healthRef.current || !notifOk.current) return;
      const r = await api.notifications(D.USER_ID);
      if (!r.ok) {
        if (r.status === 404 || r.status === 405) notifOk.current = false;
        return;
      }
      const list = r.data?.notifications || r.data?.items ||
        (Array.isArray(r.data) ? r.data : []);
      if (!Array.isArray(list)) return;
      if (seenNotifs.current === null) {           // 첫 응답은 기준선만 잡는다
        seenNotifs.current = new Set(list.map(keyOf));
        return;
      }
      for (const n of list) {
        const k = keyOf(n);
        if (seenNotifs.current.has(k)) continue;
        seenNotifs.current.add(k);
        // 우리가 방금 누른 버튼의 메아리(중복 카드) 억제
        if (Date.now() < suppressUntil.current) continue;
        push({ kind: "notif", notif: n });
      }
    }, 5000);
    return () => clearInterval(t);
  }, [push]);

  // ── 액션들 ──────────────────────────────────────────────────

  // 채팅 발화 → /chat (의도 파싱만) → 라우팅
  const send = useCallback(async (text) => {
    const msg = text.trim();
    if (!msg || !lock()) return;
    push({ kind: "user", text: msg });
    try {
      let intent = null;
      if (healthRef.current) {
        const r = await api.chat(msg, D.USER_ID);
        if (r.ok && r.data?.intent) intent = r.data.intent;
      }
      if (!intent) intent = localIntent(msg);

      if (intent === "remit" || intent === "create_mandate") {
        // LLM 의도파싱 안내 카드: 금액은 후보일 뿐, 게이트가 위임장으로 재검증 (표시 push만, 플로우 불변)
        push({ kind: "bot",
          vi: "🔍 Tôi đã phân tích yêu cầu của anh (NLP). Số tiền chỉ là đề xuất — cổng xác minh ủy quyền sẽ kiểm tra lại chính xác.",
          ko: "🔍 발화에서 의도를 파싱했습니다. 금액은 후보값일 뿐입니다. 실제 한도·수취인·조건은 게이트가 위임장으로 재검증합니다." });
        push({ kind: "bot",
          vi: "Tôi đã soạn giấy ủy quyền theo yêu cầu của anh. Hãy đọc kỹ bằng tiếng Việt rồi ký nhé.",
          ko: "요청 내용으로 위임장 초안을 만들었어요. 모국어로 꼼꼼히 확인한 뒤 서명해 주세요." });
        push({ kind: "mandate", signed: false, signing: false });
      } else if (intent === "refi") {
        push({ kind: "bot",
          vi: "Để tôi kiểm tra khoản vay của anh với điều kiện chuyển nợ của JB.",
          ko: "JB 대환 조건으로 가심사를 진행할게요. 최종 승인이 아닌 안내 단계입니다." });
        await runRefi();
      } else if (intent === "revoke") {
        await runRevoke();
      } else {
        push({ kind: "bot",
          vi: "Tôi có thể: thiết lập gửi tiền theo ủy quyền, kiểm tra chuyển nợ (giảm lãi), hoặc hủy ủy quyền.",
          ko: "위임 송금 설정, 대환 가심사, 위임 철회를 도와드릴 수 있어요." });
      }
    } finally {
      unlock();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busy, push]);

  // ① 위임장 서명: /mandate/issue → /mandate/{id}/sign (실패 시 시드 위임장 폴백)
  const sign = useCallback(async (itemId) => {
    if (!lock()) return;                   // 연타·동시 조작 시 중복 발급 방지
    suppressNotifs();                      // 서명 통지의 폴링 메아리(중복 카드) 억제
    patch(itemId, { signing: true });
    try {
      let mid = D.SEED_MANDATE_ID;
      let hash = D.SEED_ESIGN_HASH;
      if (healthRef.current) {
        // draft 필드 필수: MandateIssueRequest 스키마 준수
        const issue = await api.issueMandate({
          user_id: D.USER_ID,
          draft: {
            mandate_type: "remittance",
            language: "vi",
            beneficiary_whitelist: [
              { bnf_id: D.MOTHER.id, name: D.MOTHER.nameVi, relation: "mother",
                bank: D.MOTHER.bank, account_masked: D.MOTHER.masked },
            ],
            limits: { limit_per_tx_krw: D.REMIT_KRW, limit_monthly_krw: D.REMIT_KRW, currency_target: "VND" },
            trigger: { type: "salary_in", min_salary_krw: 500000 },
            fx_condition: { type: "better_than_ma", window_days: 7, threshold_pct: 1.0, direction: "favorable" },
            on_exception: "hold_and_ask",
            ask_timeout_min: 720,
            valid_until: "2026-12-31T23:59:59Z",
            revocation: { revocable: true, revoked: false, revoked_at: null },
            notification: { per_execution: true, channel: "in_app_push", language: "vi" },
          },
        });
        if (issue.ok && issue.data) mid = issue.data.mandate_id || issue.data.id || mid;
        const sg = await api.signMandate(mid, {
          method: "biometric_or_pin_mock", reconfirmed_in_language: true,
        });
        if (sg.ok && sg.data) {
          hash = sg.data.esign_hash || sg.data?.esign?.esign_hash || hash;
          mid = sg.data.mandate_id || mid;
        }
      }
      setMandate({ id: mid, status: "active" });
      patch(itemId, { signing: false, signed: true });
      push({ kind: "signed", mandateId: mid, hash });
      push({ kind: "bot",
        vi: "Xong! Khi lương về và tỷ giá tốt hơn ≥1% so với trung bình 7 ngày, tôi sẽ tự gửi cho mẹ, và báo anh từng lần. Anh có thể hủy bất cứ lúc nào.",
        ko: "완료! 급여가 들어오고 환율이 7일 평균 대비 1% 이상 유리하면 자동으로 송금하고, 매번 통지해 드려요. 언제든 철회하실 수 있습니다." });
    } finally {
      unlock();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patch, push]);

  // ② 급여 입금 → 위임 트리거 → 자동 송금 (실행 판정은 전적으로 백엔드 게이트)
  const salary = useCallback(async () => {
    if (!lock()) return;
    suppressNotifs();
    try {
      push({ kind: "salary", amountKrw: D.SALARY_KRW });
      setBalance((b) => b + D.SALARY_KRW);
      let outcome = null;
      // 감지 카드 → (판정 대기) → 실행 카드 순서가 화면에서 읽히도록 최소 0.9초 보장
      if (!healthRef.current) {
        outcome = await paced(Promise.resolve(D.MOCK.executed()), 900);
      } else {
        const sal = await paced(api.salaryDeposit(D.USER_ID, D.SALARY_KRW), 900);
        outcome = sal.ok ? extractOutcome(sal.data) : null;
        if (!outcome) {
          // /salary/deposit 이 집행 결과를 안 주면(또는 미구현) 직접 집행 호출
          const r = await api.executeRemittance({
            mandateId: mandateRef.current.id,
            bnfId: D.MOTHER.id,
            amountKrw: D.REMIT_KRW,
          });
          if (r.ok) outcome = r.data;
          else pushError(r.error);
        }
      }
      if (outcome) finishOutcome(outcome, { bnfLabel: D.MOTHER.label, amountKrw: D.REMIT_KRW });
    } finally {
      unlock();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [push, pushError, finishOutcome]);

  // ③ 신규 수취인 480만, 새벽 02:40 → AML 75 → 보류 + STR
  const holdAttempt = useCallback(async () => {
    if (!lock()) return;
    suppressNotifs();
    try {
      let outcome = null;
      if (!healthRef.current) {
        outcome = await paced(Promise.resolve(D.MOCK.strHold()), 650);
      } else {
        const r = await paced(api.executeRemittance({
          mandateId: mandateRef.current.id,
          bnfId: D.HOLD_BNF.id,
          amountKrw: D.HOLD_BNF.amountKrw,
          occurredAt: D.lateNightISO(),
        }), 650);
        if (r.ok) outcome = r.data; else pushError(r.error);
      }
      if (outcome) finishOutcome(outcome, { bnfLabel: D.HOLD_BNF.label, amountKrw: D.HOLD_BNF.amountKrw });
    } finally {
      unlock();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pushError, finishOutcome]);

  // ④ 사기 수취인(OTP 요구) → 블랙리스트 일치 → 즉시 차단
  const scamAttempt = useCallback(async () => {
    if (!lock()) return;
    suppressNotifs();
    try {
      let outcome = null;
      if (!healthRef.current) {
        outcome = await paced(Promise.resolve(D.MOCK.blocked()), 650);
      } else {
        const r = await paced(api.executeRemittance({
          mandateId: mandateRef.current.id,
          bnfId: D.SCAM_BNF.id,
          amountKrw: D.SCAM_BNF.amountKrw,
        }), 650);
        if (r.ok) outcome = r.data; else pushError(r.error);
      }
      if (outcome) finishOutcome(outcome, { bnfLabel: D.SCAM_BNF.label, amountKrw: D.SCAM_BNF.amountKrw });
    } finally {
      unlock();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pushError, finishOutcome]);

  // ⑤ 대환 가심사: 안내와 가심사까지 수행. 승인은 JB 심사엔진의 배타적 권한.
  const runRefi = useCallback(async () => {
    suppressNotifs();
    let offer = null;
    if (!healthRef.current) {
      offer = await paced(Promise.resolve(D.MOCK.refi()), 700);
    } else {
      const r = await paced(api.refiPrescreen(D.USER_ID), 700);
      if (r.ok) offer = r.data; else pushError(r.error);
    }
    if (offer) push({ kind: "refi", offer, applied: false, applying: false });
  }, [push, pushError]);

  const refiButton = useCallback(async () => {
    if (!lock()) return;
    try { await runRefi(); } finally { unlock(); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runRefi]);

  // [JB에 신청] → /refi/refer → 접수번호 (승인 아님)
  const refer = useCallback(async (itemId, offer) => {
    if (!lock()) return;                   // 연타 시 중복 접수 방지
    suppressNotifs();
    patch(itemId, { applying: true });
    try {
      let receipt = "JB-REF-OFFLINE1";
      let status = "received_by_jb_engine";
      if (healthRef.current) {
        const r = await api.refiRefer(D.USER_ID, {
          annual_saving_krw: offer.annual_saving_krw,
          new_monthly_krw: offer.new_monthly_krw,
          new_total_krw: offer.new_total_krw,
          late_fee_apr: offer.late_fee_apr,
          jb_product: offer.jb_product,
          jb_apr: offer.jb_apr,
          term_months: offer.term_months,
        });
        if (!r.ok) {
          pushError(r.error);
          patch(itemId, { applying: false });
          return;
        }
        receipt = r.data?.receipt_no || receipt;
        status = r.data?.status || status;
      }
      patch(itemId, { applying: false, applied: true });
      push({ kind: "receipt", receiptNo: receipt, status });
    } finally {
      unlock();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patch, push, pushError]);

  // 무조건 철회권: POST /mandate/{id}/revoke
  const runRevoke = useCallback(async () => {
    suppressNotifs();
    if (healthRef.current) {
      const r = await api.revokeMandate(mandateRef.current.id);
      if (!r.ok) { pushError(r.error); return; }
    }
    setMandate((m) => ({ ...m, status: "revoked" }));
    push({ kind: "revoked", mandateId: mandateRef.current.id });
  }, [push, pushError]);

  // 보류 카드의 모국어 질문에 대한 응답 (로컬 처리, 실행 재개는 백엔드 권한)
  const holdAnswer = useCallback((itemId, yes) => {
    patch(itemId, { answered: true });
    if (yes) {
      push({ kind: "bot",
        vi: "Đã ghi nhận xác nhận của anh. Giao dịch vẫn chờ đội AML của JB xem xét.",
        ko: "확인을 접수했습니다. 거래는 JB AML 담당자 검토 후 처리됩니다." });
    } else {
      push({ kind: "bot",
        vi: "Đã dừng an toàn. Không có khoản tiền nào được gửi đi.",
        ko: "안전하게 중단했습니다. 어떤 금액도 송금되지 않았습니다." });
    }
  }, [patch, push]);

  // 재촬영용 피드 초기화 (백엔드 DB는 python -m app.seed 로 별도 재시드)
  const reset = useCallback(() => {
    setFeed(GREETING());
    setTraces([]);
    setBalance(D.SEED_BALANCE);
    setMandate({ id: D.SEED_MANDATE_ID, status: "active" });
  }, []);

  const actions = {
    send, sign, salary, holdAttempt, scamAttempt,
    refi: refiButton, refer, revoke: runRevoke, holdAnswer, reset,
    script: () => send(D.SCRIPT_REMIT),
  };

  // ── 촬영용 단축키: F 패널 숨김/표시, 1~5 데모 단계 실행 ──
  // (채팅 입력창에 포커스가 있을 때는 무시, 한글 IME 대비 e.code 기준)
  const actionsRef = useRef(actions);
  actionsRef.current = actions;
  const tabRef = useRef(tab);
  tabRef.current = tab;
  useEffect(() => {
    const STEP_KEYS = {
      Digit1: "script", Digit2: "salary", Digit3: "holdAttempt",
      Digit4: "scamAttempt", Digit5: "refi",
      Numpad1: "script", Numpad2: "salary", Numpad3: "holdAttempt",
      Numpad4: "scamAttempt", Numpad5: "refi",
    };
    const onKey = (e) => {
      const t = e.target;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
      if (e.ctrlKey || e.altKey || e.metaKey || e.repeat) return;
      if (e.code === "KeyF") {
        e.preventDefault();
        setFilm((v) => !v);
        return;
      }
      const run = STEP_KEYS[e.code];
      if (run && tabRef.current === "customer") {
        e.preventDefault();
        actionsRef.current[run]();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className={`app ${film ? "film" : ""}`}>
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">JB</span>
          <b>마중</b>
          <span className="brand-sub">JB Bravo KOREA 안의 위임형 뱅킹 에이전트 · 송금 실행 경로에서 LLM 배제</span>
        </div>
        <nav className="tabs">
          <button className={`tab ${tab === "customer" ? "active" : ""}`}
            onClick={() => setTab("customer")}>근로자 화면</button>
          <button className={`tab ${tab === "student" ? "active" : ""}`}
            onClick={() => setTab("student")}>유학생 화면 (D-2)</button>
          <button className={`tab ${tab === "admin" ? "active" : ""}`}
            onClick={() => setTab("admin")}>관리자 대시보드 (JB)</button>
        </nav>
        <div className={`health ${healthy ? "on" : "off"}`}>
          <span className="dot" />
          {healthy ? "API 연결됨" : "오프라인 미리보기"}
        </div>
      </header>

      <main>
        <section className={tab === "customer" ? "stage" : "stage hidden"}>
          <PhoneFrame>
            <CustomerChat feed={feed} busy={busy} balance={balance}
              mandate={mandate} actions={actions} />
          </PhoneFrame>
          <ControlPanel actions={actions} busy={busy} healthy={healthy}
            onToggleFilm={() => setFilm((v) => !v)} />
        </section>

        <section className={tab === "student" ? "stage student-stage" : "stage student-stage hidden"}>
          <StudentView healthy={healthy} />
        </section>

        <section className={tab === "admin" ? "" : "hidden"}>
          <AdminDashboard traces={traces} mandate={mandate} healthy={healthy} active={tab === "admin"} />
        </section>
      </main>
      <footer className="appfoot">
        <span>마중 (Majung) · JB Fin AI Challenge MVP</span>
        <span className="sep">·</span>
        <span>자동 테스트 20/20 · 5단계 e2e</span>
        <span className="sep">·</span>
        <a href="https://github.com/moon0825/majung" target="_blank" rel="noreferrer">github.com/moon0825/majung</a>
      </footer>
    </div>
  );
}
