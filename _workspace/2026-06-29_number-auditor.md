# number-auditor 검증 보고서 (2026-06-29)

## 동결 수치 점검

| 수치 | 기준값 | 코드/문서 실제값 | 위치 | 상태 |
|---|---|---|---|---|
| FX 7일 평균 | 18.12 | `FX_SEED.ma: 18.12` | demoData.js:24 | PASS |
| FX 오늘 환율 | 18.45 | `FX_SEED.now: 18.45` | demoData.js:24 | PASS |
| FX 7일 평균 (텍스트) | 18.12 | "7일평균 18.12 대비 현재 18.45" | BusinessValuePanel.jsx:109 | PASS |
| FX 오늘 환율 (텍스트) | 18.45 | 위 동일 문자열 | BusinessValuePanel.jsx:109 | PASS |
| 대환 금리 (jb_apr) | 13.59% | `jb_apr: 0.1359` | demoData.js:BIZ.jbRefiApr | PASS |
| 대환 금리 (MOCK.refi) | 13.59% | `jb_apr: 0.1359` | demoData.js:103 | PASS |
| AML 자동통과 컷오프 | 40점 | `SCORE_HOLD = 40` | rules.py:67 | PASS |
| AML 자동보류 컷오프 | 70점 | `SCORE_STR = 70` | rules.py:68 | PASS |
| AML STR 큐 임계 (UI) | 70점 | "score ≥ 70 자동 등록" | AdminDashboard.jsx:154 | PASS |
| 연 절약액 (MOCK.refi) | 246.15만 | `annual_saving_krw: 2_461_500` | demoData.js:93 | PASS |
| 연 절약액 (BIZ) | 246.15만 | `perCapitaSavingKrw: 2_461_500` | demoData.js:172 | **수정 완료** |
| 연 절약액 (ControlPanel) | 246만 | "연 246만 원 절약" | ControlPanel.jsx:27 | PASS |

## 수정 내역

- `demoData.js:172` `perCapitaSavingKrw: 2_500_000` → `2_461_500`
- 출처맵.md 산식 "1,500만 × (30% − 13.59%) = 246.15만" 기준 정렬

## 통과 판정: PASS (수정 후)
