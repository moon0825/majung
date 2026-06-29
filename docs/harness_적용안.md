# harness 적용안 — 마중 본선 준비 "계속 개선되는 에이전트 팀"

근거: harness 레포 원문(README_KO·SKILL.md·references) + Anthropic 멀티에이전트 글 + 우리 레포 실파일 확인. 성능 주장(+60%, 15/15)은 저자 자체 측정(n=15)이고 3자 재현 미완이라 과신은 금물.

## 1. harness가 뭔가
도메인을 한 줄로 설명하면, 그 프로젝트 전용 에이전트 팀(`.claude/agents/`)과 스킬(`.claude/skills/`)을 6가지 팀 패턴 중 맞는 걸로 자동 생성한다. 트리거는 "하네스 구성해줘". 산출물이 전부 파일로 떨어져 매 세션 재사용되고, 오케스트레이터가 `_workspace/`에 중간 결과를 쌓아 다음 실행이 물려받는다. 그래서 "돌릴 때마다 조금씩 나아지는" 구조가 처음부터 들어 있다.

우리한테 좋은 이유. 본선 준비 5축(발표대본, 수치검증, 규제방어, 데모QA, 윤문)은 지금 우리가 손으로 하는 야간 개선 작업이다. harness는 이걸 역할이 갈린 팀으로 묶어주고, 이미 깐 humanize-korean 스킬과 OVERNIGHT_ROUTINE에 그대로 얹힌다.

## 2. 추천 팀 패턴: Fan-out/Fan-in + Producer-Reviewer 하이브리드 (1단계 평탄 팀)
- 5축은 같은 입력(발표덱·QnA·데모)을 서로 다른 전문성으로 동시에 점검하는 일이다. Fan-out/Fan-in이 맞다. 수치검증이 찾은 모순을 규제·대본이 바로 공유받아 같이 고친다.
- 대본·윤문은 "생성 → 검증 → 다시 쓰기"라 Producer-Reviewer다. 무한루프를 막으려 재시도는 최대 2회.
- 수치·규제·대본은 의존이 강하다(고정 수치 바뀌면 전부 갱신). 그래서 검증은 병렬, 산출은 직렬로 묶는 하이브리드가 맞다. 계층 위임은 안 쓴다(평탄한 6역할로 충분).
- 비용. 팀 모드는 단일 대비 토큰이 크게 는다. 평소엔 서브에이전트(저토큰), 교차검증 라운드만 팀 모드로. 7/3 동결 이후엔 윤문만.

## 3. 에이전트 6 + 스킬 3 설계

| 에이전트 | 역할 | 입력 | 출력 | 스킬 |
|---|---|---|---|---|
| finals-orchestrator(리더) | 작업 분배·충돌 중재·종합, PROGRESS_LOG 기록, 다음 백로그 제안 | docs 6파일 + _workspace 이전 리포트 | 종합 개선 보고 + 백로그 | 오케스트레이터 |
| pitch-scriptwriter(Producer) | 막별 멘트·오프닝/클로징 장면형 작성, 8분 배분 준수 | 발표덱·화법가이드·검증수치 | _workspace/pitch_draft.md | majung-pitch-voice |
| number-auditor(검증) | 모든 수치를 출처맵 판정·산식·pytest와 1:1 대조, 폐기수치 재등장 감시 | 발표덱·QnA·출처맵·pytest | number_report(통과/불일치/미검증) | majung-fact-guard |
| regulation-defender(검증) | QnA 방어논리를 코드/판례 근거와 1:1 유지, 새 슬라이드 모순 점검 | QnA·근거 | regulation_report | majung-regulation-map |
| demo-qa(검증) | 시연 런북과 실제 코드 동작 정합, 폴백·재시드 확인. 읽기만 | 시연스크립트·코드·빌드 | demo_qa_report | (코드 비교) |
| korean-stylist(Reviewer) | 모든 문장을 화법가이드·AI티 패턴으로 윤문. 내용·수치 무변경 | pitch_draft 등 | styled_*.md | humanize-korean(재사용) |

스킬 3종은 `majung-fact-guard`(수치↔출처맵↔산식↔pytest), `majung-regulation-map`(방어논리↔근거), `majung-pitch-voice`(화법가이드 래퍼, 윤문 엔진은 humanize-korean 재사용, 중복 생성 금지).

흐름: orchestrator가 fan-out → number·regulation·demo 동시 검증·공유 → scriptwriter가 반영해 생성 → korean-stylist 윤문(최대 2회) → orchestrator 종합·기록.

## 4. 지속 개선 루프 (harness × OVERNIGHT_ROUTINE × humanize-korean)
기존 야간 루틴 절차와 정지조건은 그대로 두고, 백로그 전진 뒤 검증 팀을 한 번 돌리는 단계만 추가한다.

매일 새벽 자동으로 개선되는 것:
1. (기존) 백로그 저위험 항목 전진, build/pytest 게이팅, 커밋.
2. (추가) finals-orchestrator 팀 1회: number-auditor가 밤새 바뀐 수치를 재대조해 회귀 적출, regulation-defender가 방어선 모순 점검, demo-qa가 런북과 코드 정합 회귀 검사(읽기만), scriptwriter→korean-stylist가 통과한 대본을 윤문.
3. 리포트를 `_workspace/`에 날짜별로 쌓고 불일치 추세를 PROGRESS_LOG에 한 줄. 이 상속이 "매일 나아짐"의 실체다.

OVERNIGHT_ROUTINE 프롬프트에 한 줄 덧붙이면 된다: "백로그 전진 후 finals-orchestrator 팀으로 docs의 대본·수치·규제·데모·윤문을 검증·개선해 _workspace에 누적, PROGRESS_LOG에 기록. 동결 구역은 읽기만, 매 변경 build/pytest 게이팅, 7/3 이후 문서·오탈자만."

검증 에이전트는 읽기만 하므로 송금 실행 경로 미수정 원칙과 충돌하지 않는다. 팀 모드는 새벽 1회만.

## 5. 설치·실행 순서
```
/plugin marketplace add revfactory/harness
/plugin install harness@harness-marketplace      # 안 되면 harness@harness 도 시도
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1     # 미설정 시 단일 에이전트로 폴백
```
"하네스 구성해줘" 트리거 시 줄 도메인 프롬프트(초안):
> 마중(외국인 근로자 위임형 뱅킹 에이전트) JB Fin:AI 본선 준비 팀을 구성해줘. 패턴은 Fan-out/Fan-in + Producer-Reviewer 하이브리드(1단계 팀). 에이전트 6: finals-orchestrator(리더), pitch-scriptwriter, number-auditor, regulation-defender, demo-qa, korean-stylist. 스킬 3: majung-fact-guard, majung-regulation-map, majung-pitch-voice. 윤문 엔진은 기존 humanize-korean 스킬 재사용(중복 생성 금지). 입력은 docs/{본선_발표덱, 본선_QnA_방어카드, 출처맵, 화법_가이드, 시연스크립트} + backend/frontend. 모든 에이전트 프롬프트에 제약을 하드코딩: 동결 구역(Gate A/B/C, lock/unlock, 오프라인 폴백, api.js throw 금지 계약, 교차 고정 수치 FX 18.12/18.45·대환 13.59%·연 246만·AML 40/70)은 읽기 전용, 본선 브랜치 claude/finals-prototype-prep-02e3b6 에서만, 매 변경 vite build/pytest 게이팅, 7/3 이후 코드 동결(문서·오탈자만). number-auditor만 수치 파일 Write, 나머지는 Read.

생성 후 사람이 검토할 것:
- `.claude/agents/*.md` 6개에 동결 규칙이 실제로 박혔는지 육안 확인
- 권한 최소화: number-auditor만 수치 파일 Write, 나머지는 Read 중심
- korean-stylist에 "내용·수치 무변경" 계약 명시
- Producer-Reviewer 재시도 최대 2회 상한
- majung-pitch-voice가 humanize-korean을 호출(윤문 엔진 중복 생성 안 함)
- 드라이런 1회: 동결 구역 안 건드리고 `_workspace`에만 리포트가 쌓이는지

## 6. 리스크·주의
1. 외부 플러그인이 `.claude/`에 코드를 자동 생성한다. 가장 큰 리스크다. 생성된 에이전트는 우리 동결 규칙을 모르니, 도메인 프롬프트에 절대규칙을 박아 넣고 생성물을 사람이 리뷰한다. 7/3 이후엔 신규 에이전트 생성 자체를 멈춘다.
2. 토큰 비용이 크다(팀 모드는 단일 대비 약 15배). 팀 라운드는 새벽 1회로 제한.
3. 동결 구역은 검증 에이전트가 읽기만 한다. demo-qa에서 Write 권한을 빼 코드를 못 고치게 한다. 고정 수치는 number-auditor만 수정 권한.
4. 보안 검사가 막을 수 있다. 플러그인 설치, 환경변수, 자동 생성 파일 커밋이 권한 프롬프트에 걸릴 수 있다. agent teams 실험 기능이 환경에서 꺼져 있으면 서브에이전트로 폴백된다(동작은 함).
5. 성능 주장은 자체 측정이다. 우리 효과는 With/Without로 직접 확인한다. 본선 D-7 안에 신규 의존을 전면 도입하지 말고, harness 팀은 "읽기 검증 + 윤문 보조"로 한정한다. 발표 핵심 산출물의 단일 진실 소스는 사람이 유지한다.
6. 윤문이 수치를 깨지 않게, korean-stylist는 항상 number-auditor 뒤에 두고 윤문 후 수치 재검증을 1패스 넣는다.

핵심 한 줄: harness로 검증 3종(수치·규제·데모) 병렬 + 대본 생성·윤문(최대 2회) 6에이전트 팀을 깔되, 읽기 검증과 윤문 보조로 한정하고 동결 규칙을 프롬프트에 박아 새벽 루틴에 얹는다.
