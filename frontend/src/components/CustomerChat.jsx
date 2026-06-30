import { useEffect, useRef, useState } from "react";
import * as D from "../demoData.js";
import { fmtNum, timeHM } from "../format.js";
import FeedItem from "./Cards.jsx";

const CHIPS = [
  { vi: D.SCRIPT_REMIT, label: "Gửi cho mẹ khi tỷ giá tốt" },
  { vi: D.SCRIPT_REFI, label: "Giảm lãi khoản vay" },
  { vi: D.SCRIPT_REVOKE, label: "Hủy ủy quyền" },
];

// 다국어 인상용 환대 인사. 근로자는 베트남어가 기본, 유학생 등 보편성은 중국어 한 컷으로 보인다.
// 완전 번역이 아니라 주고객 나라에서 그대로 쓰겠다는 감만 주는 표시 레이어 토글이다.
const WELCOME = {
  vi: { main: "Xin chào anh Minh! Chúng tôi luôn đồng hành cùng anh tại Hàn Quốc.", label: "Tiếng Việt" },
  zh: { main: "欢迎您来到韩国", label: "中文" },
};
const WELCOME_KO = "마중: 한국에 오신 분을 먼저 나가 맞이합니다";

// E-9 페르소나 첫 진입 컨텍스트 — 브로커 사채 배경(표시 레이어만, 수치는 고정값)
const PERSONA_CONTEXT = {
  vi: "Vay môi giới khi nhập cảnh: 15 triệu KRW · lãi 30%/năm",
  ko: "입국 시 브로커 사채 1,500만 · 연 30%",
};

export default function CustomerChat({ feed, busy, balance, mandate, actions }) {
  const [input, setInput] = useState("");
  const [clock, setClock] = useState(timeHM());
  const [lang, setLang] = useState("vi");
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
          JB 마중 <span>JB Bravo KOREA 안의 위임형 뱅킹 에이전트</span>
        </div>
        <div className="m-welcome">
          <div className="m-welcome-text">
            <span className="vi">{WELCOME[lang].main}</span>
            <span className="ko">{WELCOME_KO}</span>
          </div>
          <div className="lang-toggle" role="group" aria-label="언어 선택 / Ngôn ngữ / 语言">
            <button type="button" className={lang === "vi" ? "active" : ""}
              onClick={() => setLang("vi")}>{WELCOME.vi.label}</button>
            <button type="button" className={lang === "zh" ? "active" : ""}
              onClick={() => setLang("zh")}>{WELCOME.zh.label}</button>
          </div>
        </div>
        <div className="m-acct">{D.ACCOUNT_ID} · {D.USER_NAME} 🇻🇳 (E-9)</div>
        <div className="m-persona-context">
          <span className="ctx-vi">{PERSONA_CONTEXT.vi}</span>
          <span className="ctx-ko">{PERSONA_CONTEXT.ko}</span>
        </div>
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
          <FeedItem key={item.id} item={item} actions={actions} mandate={mandate} lang={lang} />
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
