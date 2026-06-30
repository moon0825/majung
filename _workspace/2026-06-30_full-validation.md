# 풀 검증 리포트 — 2026-06-30

> 매일 1회 필수 검증 3패스 결과. 읽기전용 병렬 실행.

---

## 1. number-auditor

| 항목 | 값 | 판정 |
|---|---|---|
| FX_SEED.now | 18.45 | PASS |
| FX_SEED.ma | 18.12 | PASS |
| MOCK.refi.current_apr | 0.30 (30%) | PASS |
| MOCK.refi.jb_apr | 0.1359 (13.59%) | PASS |
| MOCK.refi.annual_saving_krw | 2,461,500 | PASS |
| BIZ.loanSharkApr | 0.30 | PASS |
| BIZ.jbRefiApr | 0.1359 | PASS |
| BIZ.perCapitaSavingKrw | 2,500,000 → **수정 필요** (출처맵: 2,461,500) | FAIL → 이 사이클에서 수정 완료 |
| backend/rules.py SCORE_HOLD | 40 | PASS |
| backend/rules.py SCORE_STR | 70 | PASS |
| backend/seed.py FX MA 7일평균 | 18.12 | PASS |
| backend/seed.py 사채 원금 | 15,000,000 (1,500만) | PASS |
| backend/seed.py 사채 APR | 0.30 (30%) | PASS |
| backend/seed.py JB APR | 0.1359 (13.59%) | PASS |

**결과**: FAIL 1건 → 이 사이클에서 수정 완료 (`demoData.js` L173: 2_500_000 → 2_461_500)

---

## 2. regulation-defender

| 요구사항 | 결과 |
|---|---|
| AML 스코어 40/70 동결값 | PASS |
| Gate A→B→C 순서, 단일 경로 | PASS |
| STR_HOLD(≥70) / BLOCK(블랙리스트) | PASS |
| on_exception=hold_and_ask | PASS |
| KoFIU STR 큐 + 감사 로그 | PASS |
| 건별 통지 + 철회권 | PASS |
| 한도계좌 1회 30만원 상한 | WARN — 미구현 (데모 범위 외, 실배포 전 검토 필요) |
| 연간 해외송금 5만 달러 한도 | WARN — 미구현 (데모 범위 외) |

**결과**: 동결구역 전 항목 PASS. WARN 2건은 데모 범위 밖 (보류 목록 추가 권고).

---

## 3. demo-qa

**강점**
- 3중 게이트(A/B/C) 파이프라인 시각화 완비
- 베트남어+한국어 이중 언어 표시 작동
- 유학생 세그먼트(CNY 페어) 확장 사례 포함
- 수치 가정 투명(details 토글)

**주요 발견**
- BIZ.perCapitaSavingKrw(250만) vs MOCK.refi.annual_saving_krw(246.15만) 불일치 → 이 사이클 수정 완료
- AdminDashboard 빈 화면 위험 (시드 트레이스 없음) → 다음 사이클 백로그로 이관
- BusinessValuePanel KPI 가시성 개선 여지 → 백로그 이관

---

## 이 사이클 조치

- [x] `demoData.js` `BIZ.perCapitaSavingKrw` 2,500,000 → 2,461,500 수정 (수치 정합)
- [x] `CustomerChat.jsx` E-9 페르소나 힌트 추가 + 베트남어 인사 강화 (표시 레이어)
- [x] `styles.css` `.m-persona-hint` 클래스 추가
- [x] vite build 검증: ✓ 39 modules transformed

---

_생성: 2026-06-30, finals-orchestrator 자동 사이클_
