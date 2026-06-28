// 계좌 생애주기 stepper: 가계좌(생체인증) 다음 한도계좌 다음 정식계좌. 표시 전용.
// 자금 이동 없음. "마중은 JB가 깐 금융 인프라 위의 활성화 레이어"를 한 컷으로 보인다.

const STAGES = [
  { key: "provisional", ko: "가계좌", zh: "临时账户", sub: "생체인증 개설(인상)" },
  { key: "limited", ko: "한도계좌", zh: "限额账户", sub: "연속 급여 적립 중" },
  { key: "full", ko: "정식계좌", zh: "正式账户", sub: "한도해제 후 전체 서비스" },
];

// current: 현재 머무는 단계 key. eligible: 다음 단계로 승급 신청 가능 여부.
export default function AccountLifecycle({ current = "limited", eligible = false }) {
  const idx = STAGES.findIndex((s) => s.key === current);
  return (
    <div className="acct-lifecycle" aria-label="계좌 생애주기: 가계좌에서 정식계좌까지">
      {STAGES.map((s, i) => {
        const state = i < idx ? "done" : i === idx ? "current" : "future";
        const ready = eligible && i === idx + 1;
        return (
          <div key={s.key} className={`acct-stage ${state} ${ready ? "ready" : ""}`}>
            <div className="acct-dot">{i < idx ? "✓" : i + 1}</div>
            <div className="acct-meta">
              <div className="acct-title">{s.ko} <span className="acct-zh">{s.zh}</span></div>
              <div className="acct-sub">{s.sub}</div>
              {ready && <div className="acct-ready">해제 가능 · 可解除</div>}
            </div>
            {i < STAGES.length - 1 && <span className="acct-arrow" aria-hidden="true">→</span>}
          </div>
        );
      })}
    </div>
  );
}
