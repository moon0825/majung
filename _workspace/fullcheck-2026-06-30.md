# 하루 1회 풀 검증 결과 (2026-06-30)

3검증 에이전트 병렬 실행 완료.

---

## 1. number-auditor 검증 결과

### 통과
- [demoData.js:24] FX_SEED = { now: 18.45, ma: 18.12 } → 출처맵 FX 기준환율 18.12·실적환율 18.45와 일치
- [demoData.js:102] jb_apr: 0.1359 → 출처맵 대환 금리 13.59%와 일치
- [demoData.js:100] current_apr: 0.30 → 출처맵 사채 연 30%와 일치
- [demoData.js:174] marketSharePct: 72 → 출처맵 전북은행 외국인 신용대출 점유율 72%와 일치
- [CustomerChat.jsx:21] PERSONA_E9 = "입국 전 사채 1,500만·연 30%" → 일치
- [BusinessValuePanel.jsx:109] "+1.82% (7일평균 18.12 대비 현재 18.45)" → FX_SEED 값과 일치
- [rules.py:67-68] SCORE_HOLD = 40 / SCORE_STR = 70 → AML 컷 40/70과 일치
- [ControlPanel.jsx:27] "연 246만 원 절약" → 출처맵 B항목 일치

### 경고 → 수정 완료
- [demoData.js:172] BIZ.perCapitaSavingKrw: 2_500_000 (250만) → 출처맵 확정값 2,461,500원(246만)과 불일치
  → **이번 사이클에서 2_461_500으로 수정**

### 확인 불가
- AML 컷 40(SCORE_HOLD)은 프론트엔드 UI에 미노출 (백엔드 rules.py에만 정의)
- E-9 사채 연 20~40% 범위값 — CustomerChat은 30% 단일값으로 표기 (범위 내 값이므로 오류 아님)

---

## 2. regulation-defender 검증 결과

### 통과
- 특금법 STR·CDD·CTR: rules.py SCORE_STR=70, STR 큐 자동 등록 정상
- AML 컷 40/70: backend/app/rules.py:67-68 동결값 정확히 일치
- 게이트 순서 A→B→C: orchestrator.py 구조적 강제, 우회 경로 없음
- Lock/Unlock·busyRef: App.jsx 동결 구역 온전히 유지
- api.js throw 금지 계약: catch에서 throw 없이 { ok: false } 반환
- 최종 승인 JB 심사엔진 배타적 권한 문구: Cards.jsx, StudentView.jsx 정상 표시

### 경고 (문서 보완 권고 — 다음 사이클)
- W-1: 외국인 거주자 무증빙 연 5만 달러 한도 — 코드/문서에 미언급. SRS 제약 §5에 "JB 코어가 보증" 명시 필요
- W-2: 신규 계좌 1일 30만 원 한도 코드 미반영 — 데모 범위가 "한도계좌 해제 후 정식계좌" 시나리오임을 SRS에 명시 필요
- W-3: ControlPanel 480만 원 보류 시나리오 — 의도적 설계, 실행되지 않음. 시연 시 설명 필요

### 동결구역 이상
없음. Gate A→B→C, AML 40/70, throw 금지, lock/unlock, FX/금리 상수 모두 정상.

---

## 3. demo-qa 검증 결과

### 통과
- 다국어 vi 문구: 전체 자연스러운 관용 베트남어, 어색한 표현 없음
- E-9 페르소나 첫 화면: CustomerChat.jsx L86 상시 노출, 일관성 유지
- 빈 상태/에러: format.js 모든 포맷터 null 가드 내장, undefined 노출 없음
- 모바일 반응형 CSS: 1100px/720px breakpoint, prefers-reduced-motion 적용
- CTA 라벨: 모든 버튼 행동 유도형 문구

### 개선 권고 → 수정 완료
- B: 금리 소수점 불일치 (30.0% vs 13.59%) → fmtAPR 일원화로 수정
- C: 유학생 ④ 카드 언어 순서 역전 (한국어가 앞) → 중국어 먼저로 수정
- A: FX 환율 직접 노출 toFixed(2) 미보호 → Cards.jsx 수정

### 선택적 권고 (다음 사이클 검토)
- D: ControlPanel 제목 "데모 컨트롤 · 진행자 전용" 표기
- E: 빈 알림 폴백 "(thông báo mới · 새 알림)" 이중 표기

### 위험 (동결구역 인접)
없음.

---

## 종합 판정

| 검증 | 상태 | 조치 |
|---|---|---|
| number-auditor | 경고 1건 | 이번 사이클 수정 완료 |
| regulation-defender | 경고 3건 (W-1~W-3) | W-1·W-2 문서 보완 → 다음 사이클 |
| demo-qa | 권고 3건 | B·C·A 수정 완료, D·E 다음 사이클 |
