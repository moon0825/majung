import { useEffect, useRef, useState } from "react";
import * as D from "../demoData.js";
import { fmtNum, timeHM } from "../format.js";
import FeedItem from "./Cards.jsx";

const CHIPS = [
  { vi: D.SCRIPT_REMIT, label: "Gửi cho mẹ khi tỷ giá tốt" },
  { vi: D.SCRIPT_REFI, label: "Giảm lãi khoản vay" },
  { vi: D.SCRIPT_REVOKE, label: "Hủy ủy quyền" },
];

export default function CustomerChat({ feed, busy, balance, mandate, actions }) {
  const [input, setInput] = useState("");
  const [clock, setClock] = useState(timeHM());
  const scrollRef = useRef(null);

  // 상단 시계: 10초 주기로 갱신, 촬영 중 분 단위가 자연스럽게 흐른다
  useEffect(() => {
    const t = setInterval(() => setClock(timeHM()), 10000);
    return () => clearInterval(t);
  }, []);

  // 새 카드가 흘러들어오면 맨 아래로 (부드러운 스크롤, 모션 최소화 설정 시 즉시 이동)
  // requestAnimationFrame 미사용: 창이 가려진 상태에서도 스크롤이 누락되지 않도록 한다
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    el.scrollTo({ top: el.scrollHeight, behavior: reduced ? "instant" : "smooth" });
    // 연속 카드 추가로 스크롤이 중간에 멈춘 경우의 바닥 보정:
    // 화면이 보이는 동안은 다시 부드럽게, 가려진 상태에서는 즉시 이동
    const t = setTimeout(() => {
      if (el.scrollHeight - el.scrollTop - el.clientHeight <= 4) return;
      // CSS scroll-behavior:smooth 때문에 scrollTop 대입도 부드럽게 처리되므로
      // 즉시 이동은 behavior:"instant"를 명시해야 한다
      if (document.visibilityState === "hidden" || reduced) {
        el.scrollTo({ top: el.scrollHeight, behavior: "instant" });
      } else {
        el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
      }
    }, 700);
    return () => clearTimeout(t);
  }, [feed, busy]);

  const submit = () => {
    if (!input.trim()) return;
    actions.send(input);
    setInput("");
  };

  return (
    <>
      <div className="statusbar">
        <span>{clock}</span>
        <span>JB LTE · 100%</span>
      </div>

      <div className="m-header">
        <div className="m-bank">
          JB 마중 <span>Mandate Banking Agent</span>
        </div>
        <div className="m-acct">{D.ACCOUNT_ID} · {D.USER_NAME} 🇻🇳 (E-9)</div>
        <div className="m-balance">
          {fmtNum(balance)} <small>KRW</small>
        </div>
        <div className="m-chips">
          {mandate.status === "active" ? (
            <span className="m-chip">Ủy quyền: đang hoạt động · 위임 활성</span>
          ) : (
            <span className="m-chip revoked">Ủy quyền: đã hủy · 위임 철회됨</span>
          )}
          <span className="m-chip">{mandate.id}</span>
        </div>
      </div>

      <div className="chat" ref={scrollRef}>
        {feed.map((item) => (
          <FeedItem key={item.id} item={item} actions={actions} mandate={mandate} />
        ))}
        {busy && (
          <div className="row">
            <div className="bubble bot typing"><i /><i /><i /></div>
          </div>
        )}
      </div>

      <div className="chips">
        {CHIPS.map((c) => (
          <button key={c.label} className="chip" disabled={busy}
            onClick={() => actions.send(c.vi)}>
            {c.label}
          </button>
        ))}
      </div>

      <div className="chat-input">
        <input
          value={input}
          placeholder="Nhắn bằng tiếng Việt… (베트남어로 입력)"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
          disabled={busy}
        />
        <button onClick={submit} disabled={busy}>Gửi</button>
      </div>
    </>
  );
}
