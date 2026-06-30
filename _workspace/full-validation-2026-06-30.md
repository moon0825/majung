# 풀 검증 결과 2026-06-30

## 1. Number-Auditor

**결론**: 코드·테스트·출처맵 간 수치 일관성 확인됨. 두 가지 표기 주의 사항만 존재.

**PASS** (코드 수치 기준): FX 18.45/18.12 ✅ · 대환 13.59% ✅ · 사채 1,500만/연 30% ✅ · AML 40/70 ✅

**주의 사항**:
- 연 절약액: 코드·출처맵 모두 2,461,500원, 내부 정의는 2,460,000 표기 (산식 기준 2,461,500이 정확, 코드는 무결)
- AML 컷 방향: 정의서 "40 이하 즉시 차단" 표현이 코드 로직과 역방향. 실제: score<40→PASS, ≥40→HOLD, ≥70→STR, 블랙리스트→BLOCK. (코드는 정확, 정의서 문구 혼선)

## 2. Regulation-Defender

**PASS** (규제 준수)

- STR 자동 회부 ≥70: rules.py:68 SCORE_STR=70, orchestrator.py:116 enqueue_str_candidate ✅
- LLM 송금 실행 배제: llm.py/orchestrator.py/mcp_tools.py/api.js/SRS_v2.md 5개 파일 일관 ✅
- 특금법 CDD/KYC/CTR 출처 명기: 출처맵.md:25 ✅
- 신규 계좌 1일 30만원: 출처맵.md:17 ✅ (코드 강제는 mcp_tools에 위임)

## 3. Demo-QA

**build_pass: true, test_pass: true, test_count: 29/29**

- Vite build: 39 modules ✅
- pytest: 29 passed ✅
- 동결구역(api.js, orchestrator.py) 변경 없음 ✅
- 베트남어 대사 10문장 확인 ✅

## 종합 판정
코드베이스 무결. 정의서 문구 2건(절약액 표기·AML 방향 설명) 사람 검토 권장.
