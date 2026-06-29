import { useState } from "react";
import * as D from "../demoData.js";
import { fmtEok } from "../format.js";

// 사업가치 콘솔(관리자 전용, 한국어 단일).
// KPI는 신규 모객이 아니라 생애가치(LTV)와 대환 전환을 측정한다.
// 거시 수치는 자체 추정값이며 세션 행동과 무관하게 정적으로 표시한다(시연 일관성).

// 전환율 민감도 시나리오 (E-9 32만 × 15% × 전환율 × 1,500만 × 9.59%p)
const SCENARIOS = [
  { label: "보수", rate: 0.03, interest: 2_062_350_000 },
  { label: "기준", rate: 0.07, interest: 4_812_150_000 },
  { label: "낙관", rate: 0.12, interest: 8_249_400_000 },
];

function LockIcon() {
  return (
    <svg className="funnel-lock" width="11" height="11" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" strokeWidth="2.4" aria-hidden="true">
      <rect x="4" y="11" width="16" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </svg>
  );
}

export default function BusinessValuePanel() {
  const b = D.BIZ;
  const pct = (x) => `${Math.round(x * 100)}%`;
  const [scenIdx, setScenIdx] = useState(1); // 기본=기준(7%)

  return (
    <div className="biz-panel">
      <div className="biz-head">
        <h4>사업가치 콘솔</h4>
        <span className="biz-tag">브라보코리아 전환 엔진</span>
        <span className="biz-sub">핵심성과지표: 생애가치(LTV)와 대환 전환율. 신규 모객이 아닌 전환을 측정함</span>
      </div>

      <div className="biz-kpis">
        <div className="biz-kpi accent">
          <div className="k">대환 전환율</div>
          <div className="v">{pct(b.refiConversionRate)}</div>
          <div className="d">전환율 7% 가정(자체 추정)</div>
        </div>
        <div className="biz-kpi">
          <div className="k">대환 전환 잔액</div>
          <div className="v">{fmtEok(b.refiBalanceKrw)}</div>
          <div className="d">전환율 7% 기준 자체 추정</div>
        </div>
        <div className="biz-kpi">
          <div className="k">연 이자수익(전환분)</div>
          <div className="v">{fmtEok(b.annualInterestKrw)}</div>
          <div className="d">대환 잔액 기준 자체 추정</div>
        </div>
        <div className="biz-kpi accent">
          <div className="k">고객 1인당 연 절약액</div>
          <div className="v">{fmtEok(b.perCapitaSavingKrw)}</div>
          <div className="d">사채 연 {(b.loanSharkApr * 100).toFixed(1)}% → JB 연 {(b.jbRefiApr * 100).toFixed(2)}%</div>
        </div>
      </div>

      {/* 전환율 민감도 표 토글 — '7% 한 점 베팅' 인상 제거 */}
      <div className="biz-scenario">
        <div className="ft">수익기회 시나리오 (전환율별)</div>
        <div className="scenario-tabs" role="tablist" aria-label="전환율 시나리오">
          {SCENARIOS.map((s, i) => (
            <button
              key={s.label}
              role="tab"
              aria-selected={scenIdx === i}
              className={`scen-tab ${scenIdx === i ? "active" : ""}`}
              onClick={() => setScenIdx(i)}
            >
              {s.label} ({pct(s.rate)})
            </button>
          ))}
        </div>
        <div className="scenario-body">
          <div className="scen-row">
            <span>전환율 가정</span>
            <span className="scen-val">{pct(SCENARIOS[scenIdx].rate)}</span>
          </div>
          <div className="scen-row">
            <span>대환 전환 대상 (E-9 32만 × 부채보유 15% × 전환율)</span>
            <span className="scen-val">약 {Math.round(320_000 * 0.15 * SCENARIOS[scenIdx].rate / 1000).toLocaleString()}천 명</span>
          </div>
          <div className="scen-row">
            <span>JB 연 이자수익(차감 전, 자체 추정)</span>
            <span className="scen-val">{fmtEok(SCENARIOS[scenIdx].interest)}</span>
          </div>
          <div className="scen-note">공식: 대상 근로자 × 1인 대환잔액 1,500만 × 스프레드 9.59%p. JB 실제 데이터 입력 시 즉시 확정.</div>
        </div>
      </div>

      <details className="biz-src">
        <summary>수치 가정·산식 보기</summary>
        <div className="biz-src-body">
          <p>거시 수치는 보수적 자체 추정이며, 1인당 절약액만 확정 출처입니다.</p>
          <ul>
            <li><b>대환 전환율 {pct(b.refiConversionRate)}</b>: 휴면 다운로드와 기존 외국인 고객 가운데 대환 적격 전환 비율 가정</li>
            <li><b>대환 전환 잔액 {fmtEok(b.refiBalanceKrw)}</b>: 대상 사채 추정 잔액에 전환율 {pct(b.refiConversionRate)}를 적용한 값</li>
            <li><b>연 이자수익 {fmtEok(b.annualInterestKrw)}</b>: 전환 잔액에 JB 대환 금리 스프레드를 적용한 값</li>
            <li><b>1인당 연 {fmtEok(b.perCapitaSavingKrw)}</b>: 사채 연 {(b.loanSharkApr * 100).toFixed(1)}%와 JB 연 {(b.jbRefiApr * 100).toFixed(2)}%의 이자 차이(치트시트 확정값)</li>
          </ul>
          <p className="biz-src-note">최종 승인과 실제 실행 잔액은 JB 심사엔진 결과에 따릅니다.</p>
        </div>
      </details>

      <div className="biz-funnel">
        <div className="ft">대환 전환 퍼널 (가심사 적격에서 실행까지)</div>
        {b.funnel.map((s) => (
          <div key={s.stage} className={`funnel-row ${s.locked ? "locked" : ""}`}>
            <div className="fl">
              {s.locked && <LockIcon />}
              {s.stage}
            </div>
            <div className="funnel-track">
              <div className="funnel-fill" style={{ width: `${s.pct}%` }}>{s.pct}%</div>
            </div>
          </div>
        ))}
      </div>

      <div className="biz-loop">
        <div className="ft">검증·개선 루프 (판단 → 행동 → 검증·개선)</div>
        <div className="loop-row">
          <span className="loop-step act">행동</span>
          <span className="loop-text">최근 자동 송금의 평균 환율 우위 +1.82% (7일평균 18.12 대비 현재 18.45)</span>
        </div>
        <div className="loop-arrow">↓</div>
        <div className="loop-row">
          <span className="loop-step ver">검증</span>
          <span className="loop-text">실행 임계값 7일평균 대비 1.0% 이상이 최근 30일간 적정 작동, 오탐 0건</span>
        </div>
        <div className="loop-arrow">↓</div>
        <div className="loop-row">
          <span className="loop-step imp">개선 제안</span>
          <span className="loop-text">
            환율 변동성 확대 구간 진입 시 임계값 1.2% 이상 상향 제안.
            <span className="loop-note"> ⚠️ 임계값 변경은 자동 적용되지 않습니다. 고객이 위임장 갱신에 동의해야만 반영됩니다.</span>
          </span>
        </div>
      </div>

      <div className="biz-foot">
        승인 단계는 JB 심사엔진의 배타적 권한이며, 에이전트는 가심사와 회부까지만 수행함.
        전북은행 외국인 신용대출 점유율 {b.marketSharePct}%, 누적 {(b.cumulativeBorrowers / 10000).toFixed(0)}만 명.
        거시 수치(대환 전환 잔액 {fmtEok(b.refiBalanceKrw)}, 연 이자수익 {fmtEok(b.annualInterestKrw)}, 전환율 {pct(b.refiConversionRate)})는 자체 추정값임.
      </div>
    </div>
  );
}
