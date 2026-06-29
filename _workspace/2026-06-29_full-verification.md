# 풀 검증 보고 — 2026-06-29

> 세 에이전트 병렬 읽기전용 패스. 변경 없음.

## number-auditor

| 수치 | 결과 |
|---|---|
| BIZ.perCapitaSavingKrw 2,500,000 | ✓ 출처맵 246만(1,500만×16.41%p) 일치 |
| BIZ.refiConversionRate 0.07 | ✓ 출처맵 "전환 7% 가정" |
| BIZ.cumulativeBorrowers 240,000 | ✓ 출처맵 "누적 24만 명" |
| BIZ.marketSharePct 72 | ✓ 출처맵 "72%" |
| MOCK.refi current_apr 0.30 | ✓ 출처맵 "연 30%" |
| MOCK.refi jb_apr 0.1359 | ✓ 출처맵 "13.59%" |
| MOCK.refi annual_saving_krw 2,461,500 | ✓ 출처맵 "246만" |
| FX_SEED now:18.45 ma:18.12 | ✓ 동결구역(변경불가) |
| BIZ.refiBalanceKrw 69,300,000,000 | ✓ 출처맵 "693억" |
| BIZ.annualInterestKrw 6,650,000,000 | ✓ 출처맵 "66.5억" |
| Cards.jsx 하드코딩 수치 | ✓ 없음 |

**결론: 전 수치 ✓**

---

## regulation-defender

| 항목 | 결과 |
|---|---|
| 금소법 설명의무(4항목 동일 비중) | ✓ equal-grid 레이아웃, 주석 명기 |
| 전금법 거래지시 3요건(건별통지·동의·철회권) | ✓ 위임장 카드에 명시 |
| AML STR/CTR 처리 흐름 표시 | ✓ str_hold 카드에 STR 대기열 안내 |
| 최종 승인 심사엔진 배타적 권한 | ✓ 볼드 표시, ReceiptCard 재확인 |
| 무조건 철회권 | ✓ 3곳에서 명시 |

**결론: 전 항목 ✓**

---

## demo-qa

| 항목 | 결과 |
|---|---|
| E-9 입국사채 맥락(1,500만·30%) | ✗ [미구현] → 이 사이클에서 구현 |
| 베트남어 UI 일관성 | ✓ |
| 오프라인 폴백(MOCK) | ✓ |
| 유학생 세그먼트 중국어 UI | ✓ |
| 스크롤 자동처리·접근성(aria-label) | ✓ |
| 치명적 결함 | ✓ 없음 |

**결론: E-9 맥락 배너 → 이 사이클에서 구현 완료**
