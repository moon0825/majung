import * as D from "../demoData.js";
import { fmtEok } from "../format.js";

// 사업가치 콘솔(관리자 전용, 한국어 단일).
// KPI는 신규 모객이 아니라 생애가치(LTV)와 대환 전환을 측정한다.
// 거시 수치는 자체 추정값이며 세션 행동과 무관하게 정적으로 표시한다(시연 일관성).
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

  return (
    <div className="biz-panel">
      <div className="biz-head">
        <h4>사업가치 콘솔</h4>
        <span className="biz-tag">브라보코리아 전환 엔진</span>
        <span className="biz-tag alt">KPI: 생애가치(LTV) · 대환 전환율</span>
        <span className="biz-sub">핵심성과지표는 생애가치(LTV)와 대환 전환율로 둠. 신규 모객이 아닌 전환을 측정함</span>
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

      <div className="biz-pl">
        <div className="ft">대환 손익 효과 <span className="biz-ft-sub">전환 잔액에서 연 이자수익까지 (자체 추정)</span></div>
        <div className="pl-flow">
          <div className="pl-node">
            <div className="pl-k">대환 전환 잔액</div>
            <div className="pl-v">{fmtEok(b.refiBalanceKrw)}</div>
          </div>
          <span className="pl-conn" aria-hidden="true" />
          <div className="pl-node rev">
            <div className="pl-k">연 이자수익(전환분)</div>
            <div className="pl-v">{fmtEok(b.annualInterestKrw)}</div>
          </div>
          <span className="pl-conn" aria-hidden="true" />
          <div className="pl-node save">
            <div className="pl-k">고객 1인당 연 절약</div>
            <div className="pl-v">{fmtEok(b.perCapitaSavingKrw)}</div>
          </div>
        </div>
        <div className="pl-note">
          사채 연 {(b.loanSharkApr * 100).toFixed(1)}%에서 JB 연 {(b.jbRefiApr * 100).toFixed(2)}%로 전환할 때의 효과. 생애가치(LTV)는 전환 잔액과 이자수익으로 측정함
        </div>
      </div>

      <details className="biz-src">
        <summary>수치 가정·산식 보기</summary>
        <div className="biz-src-body">
          <p>거시 수치는 보수적 자체 추정이며, 1인당 절약액만 확정 출처입니다.</p>
          <ul>
            <li><b>대환 전환율 {pct(b.refiConversionRate)}</b>: 휴면 다운로드와 기존 외국인 고객 가운데 대환 적격 전환 비율 가정</li>
            <li><b>대환 전환 잔액 {fmtEok(b.refiBalanceKrw)}</b>: 누적 차주 {(b.cumulativeBorrowers / 10000).toFixed(0)}만 명 × 대환 침투율 가정 × 1인당 평균 대환 잔액으로 산출. {fmtEok(b.refiBalanceKrw)}은 기본 시나리오 추정이며, 침투율 가정을 낮추면 보수, 높이면 낙관 시나리오임</li>
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
          <span className="loop-text">환율 변동성 확대 구간 진입 시 임계값 1.2% 이상 상향 제안. 적용은 고객 위임장 갱신 동의가 전제</span>
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
