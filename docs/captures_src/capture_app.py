# -*- coding: utf-8 -*-
"""마중(Majung) 데모 5단계 자동 캡처, 제출 문서용 고해상도 PNG.

사전조건: 백엔드(8000)·프론트(5173) 기동 + `python -m app.seed` 재시드.
실행:    python capture_app.py
산출:    docs/captures/01~06 PNG (devicePixelRatio 3 → 폰 프레임 1242px 폭)
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = Path(r"D:\JB_Fin_AI\JB_AI Challenge\majung\docs\captures")
BASE = "http://localhost:5173"


def log(*a):
    print(*a, flush=True)


# 채팅 스크롤 컨테이너에서 txt 를 포함하는 마지막 .card 를 화면에 정렬.
# - inline style 로 smooth scroll 무력화 → scrollTo(instant)
# - React 자동 스크롤(피드 갱신 시 맨아래로)과 경합하므로 안정화 루프
ALIGN_JS = """(txt) => {
  const chat = document.querySelector('.chat');
  if (!chat) return {found:false, why:'no .chat'};
  chat.style.scrollBehavior = 'auto';
  const cards = [...chat.querySelectorAll('.card')].reverse();
  const tgt = cards.find(c => c.innerText.includes(txt));
  if (!tgt) return {found:false, why:'no card', n:cards.length};
  const chatR = chat.getBoundingClientRect();
  const top = tgt.getBoundingClientRect().top - chatR.top + chat.scrollTop;
  const want = Math.max(0, top - 8);
  chat.scrollTo({top: want, behavior: 'instant'});
  const r = tgt.getBoundingClientRect();
  return {found:true, cardH: Math.round(r.height), viewH: Math.round(chatR.height),
          scrollTop: Math.round(chat.scrollTop), want: Math.round(want),
          head: (tgt.querySelector('.card-head')||{innerText:''}).innerText.slice(0,40)};
}"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = None
        for ch in ("msedge", "chrome"):
            try:
                browser = p.chromium.launch(channel=ch, headless=True)
                log("[launch]", ch)
                break
            except Exception as e:  # noqa: BLE001
                log("[launch-fail]", ch, repr(e)[:120])
        if browser is None:
            sys.exit("no system browser channel available")

        ctx = browser.new_context(
            viewport={"width": 1720, "height": 1140},
            device_scale_factor=3,
            locale="ko-KR",
        )
        page = ctx.new_page()
        page.goto(BASE, wait_until="networkidle")
        # 실데이터 모드 확인, 백엔드 미연결이면 목 데이터라 캡처 무효
        page.wait_for_selector(".health.on", timeout=15000)
        log("[health] API 연결됨")
        # 캡처 보정: 폰 화면 844px(아이폰 13 비율), 카드 전체가 한 화면에 들어오게
        page.add_style_tag(content=".phone-screen{height:844px !important}")
        phone = page.locator(".phone")
        steps = page.locator(".step-btn")

        def idle():
            page.wait_for_selector(".chat-input button:not([disabled])", timeout=25000)
            page.wait_for_timeout(600)  # rise 애니메이션(0.28s) + smooth 자동스크롤 종료

        def show_card(txt):
            last = None
            for _ in range(6):  # React 자동 스크롤과 경합 → 위치가 2회 연속 같을 때까지
                m = page.evaluate(ALIGN_JS, txt)
                if not m.get("found"):
                    page.wait_for_timeout(300)
                    continue
                if last is not None and m["scrollTop"] == last:
                    log("[align]", txt, m)
                    return m
                last = m["scrollTop"]
                page.wait_for_timeout(350)
            log("[align-final]", txt, m)
            return m

        def js_click(selector_text):
            # 포인터 가로채기(피드 이동) 회피, DOM click 직접 디스패치
            ok = page.evaluate(
                """(txt) => {
                  const btns = [...document.querySelectorAll('.chat .card button')];
                  const b = btns.reverse().find(x => x.innerText.includes(txt) && !x.disabled);
                  if (!b) return false;
                  b.click();
                  return true;
                }""",
                selector_text,
            )
            if not ok:
                raise RuntimeError(f"button not found: {selector_text}")

        def shoot(name):
            phone.screenshot(path=str(OUT / name))
            log("[saved]", name)

        # ── ① 위임 설정: 베트남어 발화 → 위임장 카드(서명 전) ──
        steps.nth(0).click()
        page.wait_for_selector("text=Giấy ủy quyền chuyển tiền", timeout=20000)
        idle()
        show_card("Giấy ủy quyền")
        shoot("01_mandate_sign.png")

        # 서명 → 전자서명 완료 카드
        js_click("Ký")  # "Xác nhận & Ký"
        page.wait_for_selector("text=Đã ký điện tử", timeout=20000)
        idle()

        # ── ② 급여 입금 +210만 → FX +1.82% → 자동 송금 실행 ──
        steps.nth(1).click()
        page.wait_for_selector("text=Đã chuyển tiền tự động", timeout=25000)
        idle()
        show_card("Đã chuyển tiền tự động")
        shoot("02_auto_remit.png")

        # ── ③ 신규 수취인 480만·새벽 → AML 75 → 보류 + STR ──
        steps.nth(2).click()
        page.wait_for_selector("text=Tạm giữ giao dịch", timeout=25000)
        idle()
        show_card("Tạm giữ giao dịch")
        shoot("03_str_hold.png")

        # ── ④ 사기 수취인(OTP) → 블랙리스트 즉시 차단 ──
        steps.nth(3).click()
        page.wait_for_selector("text=Đã chặn giao dịch", timeout=25000)
        idle()
        show_card("Đã chặn giao dịch")
        shoot("04_scam_block.png")

        # ── ⑤ 대환 가심사, 4항목 동일 비중 고지 ──
        steps.nth(4).click()
        page.wait_for_selector("text=Đề xuất chuyển nợ sang JB", timeout=25000)
        idle()
        show_card("Đề xuất chuyển nợ")
        shoot("05_refi_offer.png")

        # [JB에 신청] → 접수번호 (감사로그 refer_to_jb_engine 적재용)
        js_click("Nộp đơn")
        page.wait_for_selector("text=Đã nộp hồ sơ cho JB", timeout=20000)
        idle()

        # ── ⑥ 관리자 대시보드: 트레이스 4건 + STR 큐 + FX 뱃지 ──
        page.locator("nav.tabs button", has_text="관리자").click()
        page.wait_for_selector("text=TRIGGER_EXECUTE", timeout=20000)
        page.wait_for_selector("text=STR-", timeout=20000)
        page.wait_for_timeout(1200)  # 감사로그 폴링 1회분 여유
        page.locator(".admin").screenshot(path=str(OUT / "06_admin_dashboard.png"))
        log("[saved] 06_admin_dashboard.png")

        browser.close()
    log("DONE")


if __name__ == "__main__":
    main()
