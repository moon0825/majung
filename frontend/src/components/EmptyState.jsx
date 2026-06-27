// 빈 상태 표시(관리자 대시보드 첫 진입용). 순수 표시 컴포넌트.
export default function EmptyState({ title, sub }) {
  return (
    <div className="empty-state">
      <svg className="es-ico" width="30" height="30" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
        <rect x="3.5" y="4.5" width="17" height="15" rx="2.2" />
        <path d="M7.5 9h9M7.5 12.5h9M7.5 16h5" />
      </svg>
      <div className="es-title">{title}</div>
      {sub && <div className="es-sub">{sub}</div>}
    </div>
  );
}
