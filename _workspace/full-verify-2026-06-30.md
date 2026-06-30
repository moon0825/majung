# 풀 검증 결과 2026-06-30

## number-auditor: PASS
- FX_SEED (18.45/18.12) ✓ demoData.js:24 ↔ SRS_v2.md 일치
- 대환 금리 13.59% ✓ demoData.js:102,176 일치
- AML 컷 40/70 ✓ rules.py:67-68 일치
- 사채 30% (20~40% 범위 내 대표값) ✓ demoData.js:175 일치
- 전북은행 점유율 72% ✓ demoData.js:174 일치

## regulation-defender: PASS
- Gate A→B→C 순서 ✓ orchestrator.py:50-137
- AML 40/70 컷오프 ✓ rules.py:67-68
- FX 18.12/18.45 ✓ seed.py:17-18
- api.js throw 금지 ✓ api.js:2 (catch에서 반환만)
- lock/busyRef/healthRef/paced/suppressNotifs ✓ App.jsx

## demo-qa: DEMO-READY
- 프론트 빌드: PASS (39모듈, 오류 없음)
- 백엔드 테스트: PASS (29 passed)
- WELCOME vi/zh ✓, 토글 버튼 ✓, CHIPS 3개 ✓, placeholder ✓
