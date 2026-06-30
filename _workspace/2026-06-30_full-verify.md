# 2026-06-30 하루 1회 풀 검증 결과

## 1. number-auditor: PASS (WARN 1건)
- FX now=18.45, ma=18.12 → OK
- jbRefiApr=0.1359 (13.59%) → OK
- loanSharkApr=0.30 (30%) → OK (출처맵 범위 20~40% 내)
- AML 컷 SCORE_HOLD=40, SCORE_STR=70 (rules.py) → OK
- marketSharePct=72 → OK
- **WARN**: BIZ.perCapitaSavingKrw=2,500,000 vs 출처맵 계산 2,461,500원 — 약 38,500원 상향 반올림. MOCK.refi.annual_saving_krw=2,461,500 정확값 존재. 표시용 BIZ 상수만 차이.

## 2. regulation-defender: PASS (frozen_zones_intact=true)
- Gate A→B→C 순서 엄격 준수 (orchestrator.py)
- lock/unlock·busyRef 패턴 정상 (App.jsx:62-71)
- 오프라인 폴백 전 액션 커버 (healthRef 분기)
- paced 타이밍 정상 (App.jsx:22, 245, 276, 297)
- STR/CDD/CTR 의무 경로 구현됨 (enqueue_str_candidate, notify_user)
- Gate C 모의값: strHold.score=75, blocked.score=100 — 백엔드 산식 정합

## 3. demo-qa: PASS (e9_persona_strength=strong)
- CustomerChat 헤더: 계정·잔액·위임 상태·언어 토글 완전
- BusinessValuePanel: KPI 4종 + 퍼널 5단계 완전
- AdminDashboard: FX·위임·STR·감사로그·파이프라인·오프라인 fallback 정상
- Cards.jsx Gate A/B/C: gateCell() 분기 로직 완전
- E-9/D-2 페르소나 분리 명확 (비자 타입·언어·통화·화면 레이어)
- **WARN 4건** (기능 결함 아님):
  - CustomerChat 언어 토글 KO 단독 경로 없음
  - Cards.jsx rejected 카드가 hold 아이콘 재사용 → 시각 혼동 가능
  - STUDENT.MOCK.tuition() message_local 누락 (COPY 테이블 우회라 런타임 오류 없음)
  - CHIPS 버튼 라벨 베트남어만 — 진행자 가독성 낮음 (ControlPanel 한국어로 보완)

## 종합: 3검증 모두 PASS. 즉각 수정 필요 항목 없음.
## 메모: BIZ.perCapitaSavingKrw 250만 vs 246.15만 차이는 다음 사이클에서 number-auditor 재검 후 조정 여부 결정.
