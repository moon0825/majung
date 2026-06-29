# 풀 검증 결과 2026-06-29

## number-auditor

| 수치 | 출처맵 | 코드 | 상태 |
|------|--------|------|------|
| FX 18.12/18.45 | PASS | demoData.js L24 | PASS |
| JB 금리 13.59% | PASS | demoData.js L102/176 | PASS |
| 연 절약 246만 | 2,461,500 | demoData.js L93 ✓, BIZ L172 수정 전 2,500,000 | FLAG → 수정완료 |
| 사채 30% | 범위 내 (20~40%) | BIZ.loanSharkApr 0.30 | PASS |
| AML 컷 70 | PASS | AdminDashboard.jsx "score ≥ 70" | PASS |

**수정**: demoData.js BIZ.perCapitaSavingKrw 2_500_000 → 2_461_500 (출처맵 일치)

## regulation-defender

| 항목 | 상태 |
|------|------|
| AML 점수 40/70 (특금법) | PASS |
| STR/CDD/CTR (KoFIU) | PASS |
| 연 5만 달러 무증빙 한도 | PASS (문서화, MVP 범위 외) |
| 신규계좌 1일 30만 원 | PASS (한도계좌 티어로 구현) |
| 위임장(mandate) 플로우 | PASS |
| 게이트 A→B→C 순서 | PASS |

## demo-qa

| 항목 | 상태 |
|------|------|
| 다국어 일관성 (vi/zh/ko) | PASS |
| E-9 페르소나 표시 | PASS (이미 🇻🇳 E-9) + 헤더 강화 이번 사이클 |
| aria-label 기본 | PASS (언어 토글 등) |
| placeholder/TODO 노출 | 경미 FLAG (Cards.jsx L450 fallback) |
| 전반적 데모 완성도 | READY FOR DEMO |

**이번 사이클 수정**: CustomerChat WELCOME.vi.main 강화 + m-context 배너 추가 (사채 1,500만·연 30%)
