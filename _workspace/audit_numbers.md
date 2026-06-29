# 수치 감사 보고서 (Number Audit Report)

감사 일시: 2026-06-29  
감사 범위: demoData.js, backend/app/rules.py, backend/app/seed.py, frontend/src/components/*.jsx, docs/출처맵.md

---

## 1. FX 환율 — 7일평균 18.12, 현재 18.45

| 파일 | 발견값 | 판정 |
|---|---|---|
| demoData.js `FX_SEED` | `{ now: 18.45, ma: 18.12, advantagePct: 1.82 }` | PASS |
| seed.py `_FX_HISTORY` | 합계 126.84 / 7 = 18.12, `_FX_NOW = 18.45` | PASS |
| AdminDashboard.jsx | `D.FX_SEED.now` / `D.FX_SEED.ma` 참조 (하드코딩 없음) | PASS |
| Cards.jsx (OutcomeCard) | `D.FX_SEED.ma` / `D.FX_SEED.now` 참조 | PASS |
| BusinessValuePanel.jsx (loop-row) | "7일평균 18.12 대비 현재 18.45" 하드코딩 텍스트 | PASS |
| ControlPanel.jsx STEP② | "FX +1.82%(7일평균 대비)" | PASS |
| docs/시연스크립트.md | "현재 18.45 / 7일 평균 18.12 / +1.82%" | PASS |

**결론: PASS** — 모든 위치에서 18.12 / 18.45 / +1.82% 일치.

---

## 2. 대환 금리 — JB 13.59%

| 파일 | 발견값 | 판정 |
|---|---|---|
| demoData.js `MOCK.refi.jb_apr` | `0.1359` | PASS |
| demoData.js `BIZ.jbRefiApr` | `0.1359` | PASS |
| seed.py `refi_products` INSERT | `0.1359` | PASS |
| rules.py (prescreen_refi 호출자) | `jb_apr` 파라미터로 전달, 하드코딩 없음 | PASS |
| 출처맵.md 수식 | `JB 13.59%` | PASS |

**결론: PASS** — 모든 위치에서 0.1359 일치.

---

## 3. 연 절약 246만 원

| 파일 | 발견값 | 판정 |
|---|---|---|
| 출처맵.md 산식 | 1,500만 × (30% − 13.59%) = 246.15만 | PASS |
| demoData.js `MOCK.refi.annual_saving_krw` | `2_461_500` (= 246.15만) | PASS |
| rules.py `prescreen_refi` | `round(principal × (current_apr − jb_apr))` → 1,500만 × 16.41% = 2,461,500 | PASS |
| ControlPanel.jsx STEP⑤ | "연 246만 원 절약" | PASS |
| **demoData.js `BIZ.perCapitaSavingKrw`** | **`2_500_000` (= 250만원)** | **FAIL** |
| BusinessValuePanel.jsx | `b.perCapitaSavingKrw` → 250만 표시 | **FAIL (파생)** |

**결론: FAIL**

- 동결 수치는 246만 원(2,461,500 KRW).
- `BIZ.perCapitaSavingKrw`는 2,500,000(250만 원)으로, 출처맵 및 MOCK.refi와 38,500원 차이.
- BusinessValuePanel의 "고객 1인당 연 절약액" KPI 카드와 "1인당 연 {fmtEok(b.perCapitaSavingKrw)}" 텍스트 모두 250만 원으로 표시된다.
- OVERNIGHT_ROUTINE.md 동결구역 명시값(연 246만)과 충돌.

---

## 4. AML 컷 — 40 (보류) / 70 (STR)

| 파일 | 발견값 | 판정 |
|---|---|---|
| rules.py `SCORE_HOLD` | `40` | PASS |
| rules.py `SCORE_STR` | `70` | PASS |
| demoData.js `MOCK.strHold.gates[C].score` | `75` (≥70 → STR_HOLD 정상) | PASS |
| AdminDashboard.jsx STR 큐 EmptyState | "AML 점수 70 이상이면 자동으로 이 대기열에 등록" | PASS |
| AdminDashboard.jsx score 뱃지 조건 | `r.score >= 70 ? "block" : "hold"` | PASS |

**결론: PASS** — 40 / 70 모두 일치.

---

## 5. 사채 — 1,500만 원, 연 30%

| 파일 | 발견값 | 판정 |
|---|---|---|
| 출처맵.md | "입국 전 사채 1,500만~2,000만 원·연 20~40%" (범위) | PASS (범위 내 대표값 사용) |
| seed.py `loans_external` INSERT | `principal=15_000_000, apr=0.30` | PASS |
| demoData.js `MOCK.refi.current_apr` | `0.30` | PASS |
| demoData.js `BIZ.loanSharkApr` | `0.30` | PASS |
| docs/시연스크립트.md V7 대사 | "연 30%의 사채 이자" | PASS |
| docs/시연스크립트.md 도입 자막 | "브로커 사채 1,500만 원, 연 30%의 고금리" | PASS |
| NIGHTLY_BACKLOG.md P2 항목 | "입국 시 브로커 사채 1,500만·연 30%" | PASS |

**결론: PASS** — 1,500만 원 / 연 30% 모두 일치.

---

## 6. 기타 수치 교차 확인

| 수치 | 출처맵/동결 | 코드 | 판정 |
|---|---|---|---|
| 전북은행 외국인 신용대출 점유율 72% | 출처맵.md A항목 | `BIZ.marketSharePct = 72` | PASS |
| 누적 차주 24만 명 | 출처맵.md A항목 | `BIZ.cumulativeBorrowers = 240_000` | PASS |
| 대환 전환율 7% 가정 | 출처맵.md B항목 | `BIZ.refiConversionRate = 0.07` | PASS |
| 대환 잔액 693억 | 출처맵.md B항목 "693억" | `BIZ.refiBalanceKrw = 69_300_000_000` | PASS |

---

## 종합 판정

| 항목 | 결과 |
|---|---|
| FX 18.12 / 18.45 | PASS |
| 대환 금리 13.59% | PASS |
| 연 절약 246만 원 | **FAIL** |
| AML 컷 40 / 70 | PASS |
| 사채 1,500만 / 연 30% | PASS |

## 전체 판정: YELLOW

### 불일치 내용 (조치 필요)

**파일**: `/home/user/majung/frontend/src/demoData.js` line 172  
**항목**: `BIZ.perCapitaSavingKrw`  
**현재값**: `2_500_000` (250만 원)  
**동결 기준값**: `2_461_500` (246.15만 원, OVERNIGHT_ROUTINE.md 동결구역·출처맵.md 산식·MOCK.refi 일치)  
**차이**: +38,500원 과장  
**영향 범위**: BusinessValuePanel.jsx의 "고객 1인당 연 절약액" KPI 카드와 관련 텍스트가 250만 원으로 표시됨. 채점 심사위원이 MOCK.refi의 246만 원과 관리자 콘솔의 250만 원을 동시에 보면 수치 불일치 지적을 받을 수 있음.

**권장 조치**: `BIZ.perCapitaSavingKrw`를 `2_461_500`으로 수정. 단, 이 값은 `fmtEok`를 통해 억 단위로 표시되므로 실제 화면 표시 결과를 확인 후 반올림 방식도 점검 필요.
