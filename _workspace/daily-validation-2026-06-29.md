# 풀 검증 리포트 · 2026-06-29

## number-auditor

| 동결 수치 | 코드 위치 | 출처맵 | 일치 |
|---|---|---|---|
| FX_SEED.now 18.45 | demoData.js L24 | 출처맵 A (교차고정) | ✅ |
| FX_SEED.ma 18.12 | demoData.js L24 | 출처맵 A (교차고정) | ✅ |
| jbRefiApr 13.59% | demoData.js L176 | 출처맵 B | ✅ |
| annual_saving_krw 246.15만 | demoData.js L95 | 출처맵 B (1인당 연 246만) | ✅ |
| AML SCORE_HOLD 40 | rules.py L67 | 동결구역 (AML 컷 40/70) | ✅ |
| AML SCORE_STR 70 | rules.py L68 | 동결구역 (AML 컷 40/70) | ✅ |
| loanSharkApr 30% | demoData.js L175 | 출처맵 A (연 20~40% 범위 내) | ✅ |
| refiConversionRate 7% | demoData.js L169 | 출처맵 B (전환 7% 가정) | ✅ |

결론: 모든 동결 수치 일치. 이상 없음.

## regulation-defender

- 특금법 STR 의무: `STR_HOLD` 결정, `str_queue` DB 기록 구현됨 ✅
- CDD: 위임장(mandate) 검증(Gate A) + 신원 확인 흐름 ✅
- 신규 계좌 30만 한도: `is_limited_account` 처리, limit_status 엔드포인트 ✅
- 외국인 무증빙 송금 연 5만 달러: 코드에 명시적 연간 누적 체크 없음 (시연 범위 초과, 경고)
  → 심사위원 질문 대비: "실 배포 시 외환 통합 시스템 연동으로 처리" 답변 준비 필요
- Gate A→B→C 순서 고정, 단일 실행 경로 불변 ✅

결론: 동결구역 규제 로직 이상 없음. 연간 송금 한도 집계는 미구현(시연 스코프 외) — Q&A 카드 필요.

## demo-qa

- vite build: 39모듈 · 빌드 1.43s · 그린 ✅
- pytest: 29개 통과 (OVERNIGHT_ROUTINE 기준 20개 이상, 증가분은 신규 테스트) ✅
- CHIPS 스크립트(SCRIPT_REMIT·REFI·REVOKE) demoData.js에 고정 ✅
- 베트남어(vi) / 중국어(zh) 토글 표시 레이어만 ✅
- 오프라인 MOCK 3종(executed/strHold/blocked/refi) 구현 ✅
- Gate A/B/C 결과 카드 표시(Cards.jsx) 확인 필요 (미실행, 다음 사이클 대면 테스트 권장)

결론: 빌드·테스트 그린. 대면 e2e는 다음 사이클 수행.
