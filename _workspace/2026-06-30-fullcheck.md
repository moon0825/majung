# 풀 검증 결과 (2026-06-30)

> 하루 1회 읽기전용 3검증 패스. 결과 요약만 기록; 동결구역 불변 확인 후 number-auditor FAIL 1건 교정.

## 1. number-auditor

| 항목 | 기준(출처맵.md §B) | 코드값 | 결과 |
|---|---|---|---|
| 1인당 절약액 | 246.15만 = 2,461,500 | `BIZ.perCapitaSavingKrw: 2_500_000` | **FAIL → 교정** |
| FX now / ma | 18.45 / 18.12 | `FX_SEED = { now: 18.45, ma: 18.12 }` | PASS |
| MOCK.refi annual_saving_krw | 2,461,500 | `annual_saving_krw: 2_461_500` | PASS |
| 대환 잔액 | 693억 | `refiBalanceKrw: 69_300_000_000` | PASS |
| 연 이자 | 66.5억 | `annualInterestKrw: 6_650_000_000` | PASS |
| AML 컷 | 40 / 70 | `SCORE_HOLD = 40` / `SCORE_STR = 70` | PASS |
| 대환 금리 | 13.59% | `jbRefiApr: 0.1359` | PASS |
| 사채 금리 | 30% | `loanSharkApr: 0.30` | PASS |

**교정 내용**: `demoData.js` BIZ.perCapitaSavingKrw 2_500_000 → 2_461_500 (출처맵 §B 산식: 1,500만×(30%−13.59%)=246.15만)

## 2. regulation-defender

| 항목 | 확인 | 결과 |
|---|---|---|
| Gate A→B→C 단일 실행 경로 | orchestrator.py 72~110행, 순서 불변 | PASS |
| STR 보류 (score≥70) | `SCORE_STR = 70`, AML 결과값 큐 등록 | PASS |
| AML HOLD (score≥40) | `SCORE_HOLD = 40` | PASS |
| 외환 한도 데모 범위 외 | demoData 연 5만달러 미노출 | WARN (데모 범위 외, 무해) |
| throw 금지 계약 | api.js 2행 "절대 throw 하지 않는다" 주석·코드 일치 | PASS |
| late_night 가산 0 | `"late_night": 0` (플래그 기록용만) | PASS |

## 3. demo-qa

| 항목 | 확인 | 결과 |
|---|---|---|
| E-9 페르소나 첫 장면 | PERSONA_E9 = "입국 전 사채 1,500만·연 30%" 표시 | PASS |
| 베트남어 인사 | WELCOME.vi.main = "Chào Minh! Chúng tôi luôn đồng hành cùng bạn" | PASS |
| 언어 토글 접근성 | role="group" aria-label="언어 선택 / Ngôn ngữ / 语言" | PASS |
| m-persona-note | CSS 존재 및 렌더 | PASS |

## 종합

- 8개 수치 중 1 FAIL → 교정 완료 (perCapitaSavingKrw)
- 동결구역(게이트 판정·lock/unlock·api.js throw 계약·고정 FX/AML 수치) 모두 미접촉
- 오픈 PR 중복 현황: PR #1(계열사 시너지·Q&A카드·런북·접근성·테스트), PR #10(발표덱 초안) → 백로그 해당 항목 건너뜀
