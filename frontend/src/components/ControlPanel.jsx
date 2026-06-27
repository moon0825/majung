// 촬영 진행자용 컨트롤 패널, 폰 옆 사이드바.
// 버튼 결과는 폰 알림 피드와 관리자 대시보드에 동시 반영된다.
const STEPS = [
  {
    n: "①", run: "script",
    label: "고객 발화 입력 (위임 설정)",
    sub: "베트남어 고정 스크립트 전송 → 위임장 카드 → 서명",
  },
  {
    n: "②", run: "salary",
    label: "급여 입금 발생 +210만원",
    sub: "감지 → FX +1.82%(7일평균 대비) → 자동 송금 + 통지",
  },
  {
    n: "③", run: "holdAttempt",
    label: "신규 수취인 480만 · 새벽 02:40",
    sub: "AML score 75 → 자동 보류 + STR 후보 큐",
  },
  {
    n: "④", run: "scamAttempt",
    label: "사기 수취인(OTP 요구) 시도",
    sub: "블랙리스트 판정 → 즉시 차단 + 경고",
  },
  {
    n: "⑤", run: "refi",
    label: "대환 가심사 실행",
    sub: "연 246만 원 절약, 동일 비중 고지 후 JB 회부",
  },
];

export default function ControlPanel({ actions, busy, healthy, onToggleFilm }) {
  return (
    <aside className="panel">
      <h3>데모 컨트롤</h3>
      <div className="panel-sub">
        촬영 진행자용: 각 버튼은 데모 5단계 시나리오를 발화와 이벤트로 주입합니다.
      </div>

      {!healthy && (
        <div className="offline-banner">
          오프라인 미리보기 모드: 백엔드(8000) 미연결.
          시드 기준 목 데이터로 레이아웃만 표시 중.
        </div>
      )}

      {busy && (
        <div className="busy-banner">
          <span className="spinner" /> 백엔드 게이트 판정 진행 중
        </div>
      )}

      {STEPS.map((s) => (
        <button key={s.n} className="step-btn" disabled={busy}
          onClick={() => actions[s.run]()}>
          <span className="step-num">{s.n}</span>
          <span>
            <span className="step-label">{s.label}</span>
            <div className="step-sub">{s.sub}</div>
          </span>
        </button>
      ))}

      <button className="film-toggle" onClick={onToggleFilm}>
        촬영 모드: 패널 숨김 (다시 표시는 F 키)
      </button>

      <button className="reset" onClick={actions.reset}>
        피드 초기화 (재촬영용)
      </button>

      <div className="panel-foot">
        단축키: <span className="mono">F</span> 패널 숨김/표시,
        숫자 <span className="mono">1~5</span> 단계 실행 (패널이 숨겨진 상태에서도 동작).
        재촬영 시 백엔드 상태(월 한도 소진·위임 철회)도 초기화 필요:
        백엔드 폴더에서 <span className="mono">python -m app.seed</span> 재실행.
      </div>
    </aside>
  );
}
