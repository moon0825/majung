import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import * as D from "../demoData.js";
import {
  fmtKRW, fmtPct, gateCell, statusMeta, timeHMS,
} from "../format.js";

// 감사로그 event_type → 뱃지 색
const EVENT_CLS = {
  gate_a: "navy", gate_b: "navy", gate_c: "navy",
  execute: "pass", notify: "na", refer_to_jb_engine: "pass",
};

function payloadSummary(json) {
  try {
    const p = JSON.parse(json);
    if (p.valid !== undefined) return `valid=${p.valid} in_scope=${p.in_mandate_scope ?? "-"}`;
    if (p.fx_decision) return `${p.fx_decision.decision} ${Number(p.fx_decision.advantage_pct).toFixed(2)}%`;
    if (p.decision) return `${p.decision} score=${p.score ?? "-"} [${(p.flags || []).join(",")}]`;
    if (p.tx_id) return `tx=${p.tx_id} ₩${Number(p.amount_krw || 0).toLocaleString()}`;
    if (p.receipt) return `receipt=${p.receipt}`;
    if (p.message) return p.message;
    const s = JSON.stringify(p);
    return s.length > 90 ? s.slice(0, 90) + "…" : s;
  } catch {
    return String(json).slice(0, 90);
  }
}

export default function AdminDashboard({ traces, mandate, healthy, active }) {
  const [fx, setFx] = useState(null);
  const [strQ, setStrQ] = useState([]);
  const [audit, setAudit] = useState([]);
  const [auto, setAuto] = useState(true);
  const [last, setLast] = useState(null);

  const refresh = useCallback(async () => {
    const [f, s, a] = await Promise.all([api.fx(), api.strQueue(), api.audit(D.USER_ID)]);
    if (f.ok && f.data?.found) setFx(f.data);
    if (s.ok) setStrQ(s.data?.queue || []);
    if (a.ok) setAudit(a.data?.logs || []);
    setLast(new Date());
  }, []);

  useEffect(() => { refresh(); }, [refresh]);
  // 탭 진입 즉시 1회 + 5초 폴링 (자동 새로고침 ON일 때)
  useEffect(() => {
    if (!active) return;
    refresh();
    if (!auto) return;
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, [auto, active, refresh]);

  const rateNow = fx?.rate_now ?? D.FX_SEED.now;
  const rateMa = fx?.rate_ma ?? D.FX_SEED.ma;
  const adv = ((rateNow - rateMa) / rateMa) * 100;
  const advOk = adv >= 1.0;

  return (
    <div className="admin">
      {/* 아키텍처 제1원칙 + 평가 용어 파이프라인 */}
      <div className="principle-strip">
        <b>송금 절차에서 LLM 배제 (할루시네이션에 따른 금융 사고 원천 차단)</b>
        <div className="pipe">
          <span>수집 (급여·FX)</span><i>→</i>
          <span>판단 (Gate A 위임장 · Gate B Rule·FX · Gate C AML)</span><i>→</i>
          <span>행동 (집행/보류/차단)</span><i>→</i>
          <span>검증·개선 (감사로그 · STR 큐)</span>
        </div>
        <div className="admin-controls">
          <label>
            <input type="checkbox" checked={auto} onChange={(e) => setAuto(e.target.checked)} />
            5초 자동
          </label>
          <button className="btn btn-ghost" onClick={refresh}>새로고침</button>
          <span style={{ opacity: 0.7 }}>
            {last ? `갱신 ${timeHMS(last)}` : "-"}{!healthy && " · 오프라인 표시값"}
          </span>
        </div>
      </div>

      {/* 상단 통계 카드 */}
      <div className="stat-row">
        <div className="stat-card">
          <div className="t">FX 현황 (KRW/VND)</div>
          <div className="big">{rateNow.toFixed(2)} <small>VND/KRW</small></div>
          <div className="sub2">7일평균 {rateMa.toFixed(2)} · 임계 ≥1%</div>
          <div style={{ marginTop: 8 }}>
            <span className={`badge ${advOk ? "pass" : "hold"}`}>
              {fmtPct(adv)} {advOk ? "조건 충족: TRIGGER_EXECUTE" : "조건 미달: WAIT"}
            </span>
          </div>
        </div>
        <div className="stat-card">
          <div className="t">위임장 상태</div>
          <div className="big" style={{ fontSize: 17 }}>{mandate.id}</div>
          <div style={{ marginTop: 8 }}>
            {mandate.status === "active"
              ? <span className="badge pass">ACTIVE (전자서명, 건별 통지, 철회권 내장)</span>
              : <span className="badge block">REVOKED (무조건 철회 처리됨)</span>}
          </div>
        </div>
        <div className="stat-card">
          <div className="t">STR 후보 큐</div>
          <div className="big">{strQ.length}<small> 건</small></div>
          <div className="sub2">score ≥ 70 자동 등록 · 보류 우선</div>
        </div>
        <div className="stat-card">
          <div className="t">게이트 판정 (이번 세션)</div>
          <div className="big">{traces.length}<small> 건</small></div>
          <div className="sub2">감사로그 {audit.length}건 적재</div>
        </div>
      </div>

      {/* 게이트 판정 트레이스 */}
      <div className="table-card">
        <h4>게이트 판정 트레이스 <span className="cnt">판단 → 행동, 모든 판정은 결정적 코드가 수행</span></h4>
        <table>
          <thead>
            <tr>
              <th>시간</th><th>수취인</th><th>금액</th>
              <th>Gate A 위임장</th><th>Gate B Rule·FX</th><th>Gate C AML</th>
              <th>최종 상태</th>
            </tr>
          </thead>
          <tbody>
            {traces.length === 0 ? (
              <tr><td colSpan={7} className="empty-row">
                아직 판정 내역이 없습니다. 고객 화면의 데모 컨트롤 버튼을 누르면 실시간 반영됩니다.
              </td></tr>
            ) : traces.map((t, i) => {
              const m = statusMeta(t.outcome.status);
              return (
                <tr key={i}>
                  <td className="mono" style={{ background: "none" }}>{timeHMS(t.ts)}</td>
                  <td>{t.bnf}</td>
                  <td>{fmtKRW(t.amountKrw)}</td>
                  {["A", "B", "C"].map((g) => {
                    const c = gateCell(t.outcome, g);
                    return <td key={g}><span className={`badge ${c.cls}`}>{c.text}</span></td>;
                  })}
                  <td><span className={`badge ${m.cls}`}>{m.ko}</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="two-col">
        {/* STR 후보 큐 */}
        <div className="table-card">
          <h4>STR 후보 대기열 <span className="cnt">AML 연계: 의심 탐지가 자동 실행에 우선</span></h4>
          <table>
            <thead>
              <tr><th>ID</th><th>score</th><th>flags</th><th>상태</th></tr>
            </thead>
            <tbody>
              {strQ.length === 0 ? (
                <tr><td colSpan={4} className="empty-row">
                  큐 비어 있음{!healthy && " (백엔드 미연결)"}
                </td></tr>
              ) : strQ.map((r) => {
                let flags = [];
                try { flags = JSON.parse(r.flags); } catch { flags = [String(r.flags)]; }
                return (
                  <tr key={r.id}>
                    <td className="mono" style={{ background: "none" }}>STR-{r.id}</td>
                    <td><span className={`badge ${r.score >= 70 ? "block" : "hold"}`}>{r.score}</span></td>
                    <td>
                      <div className="flags">
                        {flags.map((f) => <span key={f} className="flag-chip">{f}</span>)}
                      </div>
                    </td>
                    <td><span className="badge hold">{r.status}</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* 감사로그 */}
        <div className="table-card">
          <h4>감사로그 ({D.USER_ID}) <span className="cnt">검증·개선: 설명 가능성과 책임 소재 확보</span></h4>
          <div className="audit-list">
            {audit.length === 0 ? (
              <div className="empty-row">로그 없음{!healthy && " (백엔드 미연결)"}</div>
            ) : audit.map((l) => (
              <div className="audit-item" key={l.log_id}>
                <span className="time">{(l.created_at || "").slice(11, 19) || "-"}</span>
                <span className={`badge ${EVENT_CLS[l.event_type] || "navy"}`}>{l.event_type}</span>
                <span className="payload">{payloadSummary(l.payload_json)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
