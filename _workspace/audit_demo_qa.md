# 마중 데모 QA 감사 보고서

감사 일자: 2026-06-29
감사 범위: frontend/src/components/*.jsx, frontend/src/App.jsx, frontend/src/demoData.js
기준 문서: docs/시연스크립트.md

---

## 총평: YELLOW

5개 시퀀스 중 4개가 READY, 1개(⑤)는 PARTIAL.
V1~V10 중 8개가 표시 레이어에 직접 노출되고 2개(V4, V7)는 구조상 노출되지 않음.
페인포인트 "사채 1,500만·연 30%"는 CustomerChat에 정적 문자열로 존재하나
영상에서 가장 먼저 등장하는 도입 자막(검은 화면 3장) UI는 없음.
핵심 데모 동선(①~④)은 모두 갖춰져 있고 채점 위험 요소는 ⑤와 도입 자막이다.

---

## 시퀀스별 판정

### 시퀀스 ① 위임 설정 — READY

| 체크 항목 | 결과 |
|---|---|
| V1 발화 → 위임장 카드 생성 | ControlPanel STEP ① `send(D.SCRIPT_REMIT)` → `push({kind:"mandate"})` 정상 동작. SCRIPT_REMIT = "Khi có lương, nếu tỷ giá tốt, gửi 2 triệu KRW cho mẹ tôi nhé." (V1 의미 동일) |
| 위임장 카드: 수취인, 한도 200만, 환율 조건, 철회권 | Cards.jsx MandateCard에 4개 항목 모두 베트남어+한국어 병기로 노출 |
| V2 모국어 재확인 흐름 | 서명 버튼에 "Xác nhận & Ký / 재확인 후 서명" 카피, SignedCard에 "모국어 재확인을 마쳤습니다" 노트 존재. V2("Đây là gì? 베트남어로 보여주세요") 자체 문장은 채팅 피드에 칩/버튼으로 고정되지 않음 — 촬영자가 직접 타이핑해야 함 |
| V3 서명 완료 + 해시 노출 | SignedCard에 `mandateId`, `esign_hash`(sha256: 접두어 포함) 노출 |
| 베트남어+한국어 병기 자막 | 전 카드에 `.vi` / `.ko` 2중 렌더링 |

미비: V2 문장이 채팅 입력칩에 없어 촬영자가 손으로 타이핑해야 한다. 표시 레이어 추가로 해소 가능.

---

### 시퀀스 ② 자동 송금 (Gate A·B·C) — READY

| 체크 항목 | 결과 |
|---|---|
| Gate A·B·C PASS 카드 | OutcomeCard `GatePills` 컴포넌트가 A/B/C 3개 게이트를 뱃지로 표시 |
| FX 수치 18.45 / 7일평균 18.12 / +1.82% | `FX_SEED = { now: 18.45, ma: 18.12, advantagePct: 1.82 }` — 카드 본문 `apr-compare` 영역에 렌더링 |
| V4 환율 브리지("Tỷ giá hôm nay thế nào?") | 고정 칩에 없음. "Gửi cho mẹ khi tỷ giá tốt" 칩만 존재. V4는 별도 타이핑 필요 |
| V6 철회권 확인("Tôi có thể hủy bất cứ lúc nào không?") | 철회 버튼 "Hủy ủy quyền / 위임 철회 (무조건, 즉시 처리)" 상시 노출, 문구가 V6 취지와 일치 |
| 고객 개입 없는 자동 실행 연출 | "자동 송금 실행 (고객 개입 없음)" 헤드 뱃지, AUTO 태그, auto-steps(급여 감지→게이트 통과→자동 송금) 노출. 촬영 중 커서 숨김은 ControlPanel의 '촬영 모드' 버튼(F키)으로 지원 |

---

### 시퀀스 ③ STR 보류 — READY

| 체크 항목 | 결과 |
|---|---|
| AML score 75 보류 카드 | OutcomeCard `held`/`str_hold` 분기: score 뱃지, FlagChips, STR 대기열 등록 노트 |
| V5 발화("Đây không phải người tôi muốn gửi") | 보류 카드 내 모국어 질문 버튼 "Không, dừng lại / 아니요, 중단합니다" 존재. V5 고정 문장 자체는 채팅 칩에 없음 — 촬영자 타이핑 필요 |
| 관리자 대시보드 STR 대기열 | AdminDashboard에 STR 후보 대기열 테이블 + 5초 자동 폴링. AML score 기준 표시 |

---

### 시퀀스 ④ 사기 차단 — READY

| 체크 항목 | 결과 |
|---|---|
| 블랙리스트 즉시 차단 카드 | OutcomeCard `blocked` 분기: "블랙리스트 즉시 차단" 뱃지, OTP 경고 베트남어+한국어 |
| 차단 카드 OTP 경고 문구 | "OTP, 신분증, 선입금을 요구하는 거래는 사기 패턴으로 판정되어 즉시 차단되었습니다." 노출 |
| 관리자 대시보드 게이트 판정 트레이스 | 실시간 업데이트 테이블, 건별 Gate A/B/C 판정 뱃지 |

---

### 시퀀스 ⑤ 대환 제안 — PARTIAL

| 체크 항목 | 결과 |
|---|---|
| V7 발화("Tôi đang trả lãi 30% một năm") | 고정 칩 없음. HINTS.refi 배열에 "사채", "vay", "nợ", "lãi" 포함돼 lãi(이자) 입력 시 대환 플로 진입은 가능하나, V7 고정 문장 칩은 부재. 촬영자 타이핑 필요 |
| V8 질문("Tôi có thể tiết kiệm bao nhiêu?") | 별도 칩 없음 |
| 분석 카드 → 대환 제안 카드 | RefiCard: 연 절약액 `annual_saving_krw` 렌더링(demoData 값 2,461,500원 = 약 246만 원) |
| 절약액 + 월 상환액 동일 크기 고지 (금소법) | `equal-grid` 4셀 구조(연 절약액, 새 월상환액, 총상환액, 연체가산금리) 동일 CSS 클래스로 균등 노출. 스크립트 요구사항 충족 |
| V9 회부("Nộp đơn cho ngân hàng JB") | 대환 카드 버튼 "Nộp đơn cho JB / JB에 신청" — V9와 의미 일치. 고정 문장 자체는 타이핑 필요 |
| 접수번호 노출 | ReceiptCard `receiptNo` 노출 |
| 최종 승인은 JB 심사엔진 강조 | RefiCard와 ReceiptCard 양쪽에 명시 |

부족: ControlPanel STEP ⑤의 sub 텍스트에 "연 246만 원 절약"이 명시돼 있으나, `demoData.MOCK.refi.annual_saving_krw = 2_461_500`으로 실제 계산값 246.15만 원과 일치. 다만 V7·V8 발화 칩이 없어 촬영자가 두 줄을 타이핑해야 하며, ②처럼 자동 연출이 아니라 대화 흐름이 끊길 수 있음.

---

## V1~V10 베트남어 구문 노출 현황

| 번호 | 문장 첫 어절 | 노출 방식 | 판정 |
|---|---|---|---|
| V1 | Lương về thì gửi cho mẹ… | `demoData.SCRIPT_REMIT` 칩 버튼 "Gửi cho mẹ khi tỷ giá tốt"로 연결. 고정 문장과 약 차이 있으나 동일 의미 | PARTIAL (발화 트리거됨, 구문 정확도 차이) |
| V2 | Đây là gì? Tiếng Việt. | 채팅 칩·카드 미노출. 촬영자 직접 타이핑 필요 | MISSING |
| V3 | Tôi đồng ý. Ký xác nhận. | MandateCard 서명 버튼 및 SignedCard에 "Đã ký · 서명 완료" 노출 | READY |
| V4 | Tỷ giá hôm nay thế nào? | 채팅 칩 없음. 타이핑 필요 | MISSING |
| V5 | Đây không phải người tôi muốn gửi | 보류 카드 내 "Không, dừng lại" 버튼 (의미 일치). V5 전체 문장 칩 없음 | PARTIAL |
| V6 | Tôi có thể hủy bất cứ lúc nào | 위임장 카드 "Quyền hủy: Hủy bất cứ lúc nào, vô điều kiện" + 철회 버튼 | READY |
| V7 | Tôi đang trả lãi 30% một năm | 칩 없음. `lãi` 키워드가 HINTS.refi에 있어 타이핑하면 작동 | PARTIAL |
| V8 | Tôi có thể tiết kiệm bao nhiêu? | 칩 없음. 타이핑 필요 | MISSING |
| V9 | Nộp đơn cho ngân hàng JB | 대환 카드 버튼 "Nộp đơn cho JB" (의미 일치, 전체 문장 아님) | PARTIAL |
| V10 | Cảm ơn. Giờ tôi có lịch sử tín dụng | 칩 없음. 클로징 연출 없음 | MISSING |

노출: V3·V6 READY / V1·V5·V7·V9 PARTIAL / V2·V4·V8·V10 MISSING

---

## 페인포인트 "사채 1,500만·연 30%" 표시 여부

`CustomerChat.jsx` 19번 줄:
```
const PAIN_NOTE_VI = "입국 시 브로커 사채 1,500만·연 30%";
```
77번 줄:
```
{lang === "vi" && <span className="m-pain-note">{PAIN_NOTE_VI}</span>}
```

판정: 표시 레이어에 존재. 언어 토글이 "vi"일 때 폰 헤더 영역에 렌더링됨.
단, 스크립트 도입부 "검은 화면 자막 3장"(0:00~0:25)은 UI 컴포넌트로 구현되지 않고 영상 편집 레이어에서 처리할 것으로 가정됨. UI 안에서 이 도입 자막을 재현하는 컴포넌트는 없음.

---

## 표시 레이어 추가로 해소 가능한 항목

1. **V2·V4·V8·V10 채팅 칩 추가**: `CustomerChat.jsx`의 CHIPS 배열에 4개 고정 발화 칩 추가. App.jsx의 localIntent 힌트에 "Đây là gì", "tiếng Việt", "tiết kiệm", "lịch sử" 키워드 추가.

2. **V7 전체 문장 칩 추가**: "Tôi đang trả lãi 30% một năm" 칩 추가. 현재 HINTS.refi의 "lãi"로 트리거되나 고정 문장 칩이 없으면 촬영 시 타이핑 오류 위험 있음.

3. **V1 칩 문장 동기화**: 현재 칩 레이블 "Gửi cho mẹ khi tỷ giá tốt"는 고정 발화 V1 "Lương về thì gửi cho mẹ, khi tỷ giá tốt, tối đa 2 triệu"와 다름. `demoData.SCRIPT_REMIT` 값 또는 칩 표시 레이블 통일.

4. **도입 자막 컴포넌트**: 스크립트 0:00~0:25의 "입국 전 떠안은 브로커 사채 1,500만 원, 연 30%의 고금리" 등 3장 자막을 UI 내 오버레이 또는 별도 인트로 화면으로 구현 가능. 현재 없음.

---

## 파일 위치 요약

| 파일 | 핵심 역할 |
|---|---|
| `/home/user/majung/frontend/src/components/Cards.jsx` | 전 카드 유형 렌더링 (위임장, 서명, 급여, 송금결과, 대환, 접수) |
| `/home/user/majung/frontend/src/components/CustomerChat.jsx` | 폰 채팅 UI, 언어 토글, 페인포인트 노트, 채팅 칩 |
| `/home/user/majung/frontend/src/components/ControlPanel.jsx` | 촬영 진행자 패널, 5단계 버튼, F키 패널 숨김 |
| `/home/user/majung/frontend/src/components/AdminDashboard.jsx` | STR 대기열, 게이트 판정 트레이스, 감사로그 |
| `/home/user/majung/frontend/src/components/BusinessValuePanel.jsx` | 사업가치 KPI, 대환 퍼널, 사채→JB 절약액 |
| `/home/user/majung/frontend/src/demoData.js` | 고정 시드값 (FX_SEED, MOCK, BIZ, STUDENT) |
| `/home/user/majung/frontend/src/App.jsx` | 액션 오케스트레이션, 의도 파싱, 단축키 |
