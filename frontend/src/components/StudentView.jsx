import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import * as D from "../demoData.js";
import { fmtNum, fmtPct, gateCell, GATE_NAME } from "../format.js";
import AccountLifecycle from "./AccountLifecycle.jsx";

// ───────────────────────────────────────────────────────────────
// v2 유학생 surface (둘째 입구). 근로자 채팅과 완전히 분리된 표시 레이어다.
// 송금 실행 경로(3중 게이트)는 동일한 백엔드 run_remittance를 KRW/CNY로 재사용할 뿐,
// 이 컴포넌트는 결과를 보여줄 뿐 실행 여부를 결정하지 않는다(App의 lock/busy와도 무관).
// ───────────────────────────────────────────────────────────────

// 근로자 화면의 paced 연출과 같은 "감지→판정→실행" 가독 간격을, 여기서는 별도 로컬 함수로 둔다.
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const paced = async (promise, ms) => (await Promise.all([promise, wait(ms)]))[0];

const S = D.STUDENT;

export default function StudentView({ healthy }) {
  const healthyRef = useRef(healthy);
  healthyRef.current = healthy;

  const [limit, setLimit] = useState(null);
  const [credit, setCredit] = useState(null);
  const [tuition, setTuition] = useState(null);   // 등록금 송금 outcome
  const [busy, setBusy] = useState(false);
  const [applied, setApplied] = useState(false);  // 한도해제 신청(인상)
  const busyRef = useRef(false);

  // ── 초기 로드: 한도해제 코치 + 신용 스냅샷 (오프라인이면 목) ──
  useEffect(() => {
    let alive = true;
    (async () => {
      if (healthyRef.current) {
        const [l, c] = await Promise.all([
          api.limitStatus(S.USER_ID),
          api.creditProfile(S.USER_ID),
        ]);
        if (!alive) return;
        setLimit(l.ok ? l.data : D.STUDENT.MOCK.limitStatus());
        setCredit(c.ok ? c.data : D.STUDENT.MOCK.creditProfile());
      } else {
        if (!alive) return;
        setLimit(D.STUDENT.MOCK.limitStatus());
        setCredit(D.STUDENT.MOCK.creditProfile());
      }
    })();
    return () => { alive = false; };
  }, [healthy]);

  // ── ① 등록금 송금 (실동작): 동일 3중 게이트 재사용(KRW/CNY) ──
  const runTuition = useCallback(async () => {
    if (busyRef.current) return;
    busyRef.current = true;
    setBusy(true);
    try {
      let outcome = null;
      if (!healthyRef.current) {
        outcome = await paced(Promise.resolve(D.STUDENT.MOCK.tuition()), 900);
      } else {
        const r = await paced(api.tuitionExecute({
          mandateId: S.MANDATE_ID, bnfId: S.UNIV.id, amountKrw: S.TUITION_KRW,
        }), 900);
        outcome = r.ok ? r.data : D.STUDENT.MOCK.tuition();
      }
      setTuition(outcome);
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }, []);

  const lifecycleEligible = !!limit?.eligible;
  const copy = tuition ? (D.STUDENT.COPY[tuition.status] || D.STUDENT.COPY.rejected) : null;

  return (
    <div className="student-view">
      <header className="student-hd">
        <div className="student-id">
          <span className="seg-badge">유학생 · 留学生</span>
          <b>{S.NAME}</b>
          <span className="student-sub">{S.VISA} 비자 · 中文/한국어 · 한도계좌</span>
        </div>
        <div className="student-tag">같은 엔진, 두 입구 — 등록금 송금은 동일 3중 게이트(KRW/CNY)</div>
      </header>

      {/* 계좌 생애주기: 가계좌 → 한도계좌(현재) → 정식계좌 */}
      <section className="student-card">
        <div className="student-card-hd">계좌 활성화 단계 <span className="zh">账户激活阶段</span></div>
        <AccountLifecycle current="limited" eligible={lifecycleEligible} />
        <p className="student-note">JB가 깐 가계좌·한도계좌 위에서, 마중은 "언제 한도해제가 가능한지"를 코치합니다. 자금 이동 없음.</p>
      </section>

      <div className="student-grid">
        {/* ① 등록금 위임 송금 */}
        <section className="student-card">
          <div className="student-card-hd">① 등록금 자동 송금 <span className="zh">学费自动汇款</span></div>
          <div className="student-row">
            <div>
              <div className="amount-big">{fmtNum(S.TUITION_KRW)} KRW</div>
              <div className="amount-sub">{S.UNIV.labelZh} · {S.UNIV.labelKo}</div>
            </div>
            <div className="fx-chip">环率 {fmtPct(S.FX_CNY.advantagePct)} (7日평균 대비)</div>
          </div>

          {!tuition ? (
            <button className="btn btn-primary" disabled={busy} onClick={runTuition}>
              {busy ? "处理中…" : "环率 좋을 때 등록금 보내기"}
              <span className="ko-btn">3중 게이트 통과 시에만 실행</span>
            </button>
          ) : (
            <div className={`tuition-result ${tuition.status === "executed" ? "ok" : "warn"}`}>
              <div className="tuition-title">{copy.zh} <span className="ko">{copy.ko}</span></div>
              <div className="gates">
                {["A", "B", "C"].map((g) => {
                  const c = gateCell(tuition, g);
                  return (
                    <span key={g} className={`gate-pill ${c.cls}`}>
                      Gate {g} {GATE_NAME[g]} · {c.text}
                    </span>
                  );
                })}
              </div>
              {tuition.tx_id && (
                <div className="student-note">TX <span className="mono">{tuition.tx_id}</span> · 한패스 레일(모의) · 건별 통지(中文)</div>
              )}
            </div>
          )}
        </section>

        {/* ② 한도해제 코치 (실동작 read-only) */}
        <section className="student-card">
          <div className="student-card-hd">② 한도해제 코치 <span className="zh">限额解除指引</span></div>
          {limit ? (
            <>
              <div className="limit-meter" aria-label="연속 급여 입금 진행률">
                {Array.from({ length: limit.min_months }).map((_, i) => (
                  <span key={i} className={`limit-pip ${i < limit.months_consecutive ? "on" : ""}`} />
                ))}
                <span className="limit-count">{limit.months_consecutive}/{limit.min_months}개월</span>
              </div>
              <div className="student-msg">{limit.message_local}</div>
              <div className="student-msg ko">{limit.message_ko}</div>
              {limit.eligible ? (
                applied ? (
                  <span className="done-chip">신청 접수됨 · 已申请</span>
                ) : (
                  <button className="btn btn-primary" onClick={() => setApplied(true)}>
                    정식계좌 전환 신청 <span className="ko-btn">申请转为正式账户</span>
                  </button>
                )
              ) : (
                <div className="student-note">{limit.remaining_months}개월 더 쌓이면 해제 가능합니다.</div>
              )}
            </>
          ) : <div className="student-note">불러오는 중…</div>}
        </section>

        {/* ③ 재학중 신용형성 (인상 스냅샷) */}
        <section className="student-card">
          <div className="student-card-hd">③ 재학중 신용형성 <span className="zh">在学期间信用积累</span></div>
          {credit ? (
            <>
              <div className="credit-step">{credit.credit_step}</div>
              <div className="credit-stats">
                <div><b>{credit.months_consecutive}</b><span>연속 급여(개월)</span></div>
                <div><b>{credit.on_time_ratio_pct}%</b><span>정시 거래</span></div>
              </div>
              <div className="student-msg">{credit.message_local}</div>
              <div className="student-msg ko">{credit.message_ko}</div>
            </>
          ) : <div className="student-note">불러오는 중…</div>}
        </section>

        {/* ④ 졸업전환 가심사 (인상·재사용 준비) — 원화 절약 헤드라인 미노출 */}
        <section className="student-card">
          <div className="student-card-hd">④ 졸업 후 신용 전환 <span className="zh">毕业后信用衔接</span></div>
          <div className="grad-ready">
            <span className="done-chip">가심사 적격 · 가등급 B</span>
          </div>
          <div className="student-msg">졸업·취업 비자 전환 시, 재학중 쌓은 급여·거래 이력으로 대환 가심사를 바로 진행할 수 있도록 준비됩니다.</div>
          <div className="student-msg ko">毕业并转换工作签证时，可凭在学期间积累的工资与交易记录直接进行贷款预审。</div>
          <div className="student-note"><b>최종 승인은 전북은행 심사엔진의 배타적 권한</b>입니다.</div>
        </section>
      </div>

      <footer className="student-foot">
        스테이블코인 등록금 정산 · CB(외국인 신용평가) 연계는 로드맵(Future Work)입니다. 본 데모는 활성화 레이어까지 시연합니다.
      </footer>
    </div>
  );
}
