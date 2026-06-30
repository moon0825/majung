# 새벽 자동 개발 루틴 (마중 / JB 본선)

> Anthropic 클라우드에서 **90분마다** 자동 실행되는 Claude Code **Routine**이 그대로 따르는 작업 지침.
> 목적: 본선(7/4~5) 전까지 90분 사이클마다 작은 덩어리를 안전하게 전진시킨다. finals-orchestrator가 매 사이클을 지휘·감독한다.
> 한 사이클은 작게 끝내고 멈춘다(할당량을 한 방에 태우지 않음). **매 항목 빌드/테스트 게이팅 + 드리프트 점검**으로 브랜치는 항상 그린.

---

## A. 루틴 켜는 법 (사람이 1회만 — 약 2분)

새벽 자동 실행의 정답은 **Claude Code on the web의 Routines** 다. 노트북이 꺼져 있어도 클라우드에서 돈다.
(세션 안의 CronCreate는 컨테이너가 비활성 시 회수되어 밤새 실행이 안 되므로 부적합 — 반드시 Routine 사용.)

**방법 1 — 웹 UI (권장):** [claude.ai/code/routines](https://claude.ai/code/routines) → **New routine**
- **Name:** `마중 자동 개발 (90분 사이클)`
- **Prompt (그대로 붙여넣기):** 이 루틴은 **90분마다 도는 짧은 한 사이클**이다. 한 번에 다 하려 하지 말고, finals-orchestrator가 작고 완결된 한 덩어리만 계획·배정·실행·감독한다. "이상한 데로 빠지지 않게" 매 사이클 드리프트 점검을 한다.
  ```
  너는 마중(Majung) 자율 개발의 진행을 지휘·감독하는 finals-orchestrator다. 이 세션은 90분에 한 번
  도는 '한 사이클'이다. 한 번에 다 하려 하지 마라. 작고 완결된 한 덩어리만 제대로 끝내고 멈춰라.
  다음 사이클이 90분 뒤 이어받는다. JB 본선(7/4~5) 1등이 목표.

  [0. 감독 원칙] 너는 실행자이자 감독이다. 커밋 전 매번 스스로 점검한다: (1) 동결구역을 건드렸나?
  (2) 수치가 docs/출처맵.md와 어긋났나? (3) 화법(docs/화법_가이드.md)을 어겼나? (4) 빌드·테스트가
  그린인가? 하나라도 어긋나면 그 변경을 폐기(git checkout -- .)하고 PROGRESS_LOG에 사유를 남긴다.
  억지로 밀지 마라. 의심스러우면 안 하는 게 맞다.

  [1. 상태 파악] 읽어라: CLAUDE.md, OVERNIGHT_ROUTINE.md, NIGHTLY_BACKLOG.md, PROGRESS_LOG.md
  최근 5건(직전 사이클이 뭘 했나 — 중복 금지), 필요시 docs/본선_발표덱.md·docs/출처맵.md.
  본선 브랜치 claude/finals-prototype-prep-02e3b6 체크아웃·최신화부터.

  [2. 이번 사이클 목표 (작게)] 백로그에서 저위험 항목 1~3개, 또는 큰 작업의 '한 조각'만 고른다.
  예: 발표덱 v5는 한 사이클에 한 섹션만 _workspace/에 초안. 위험'중'·[!]·[!→리뷰]는 절대 안 건드린다.
  목표를 PROGRESS_LOG 맨 위 '사이클 계획' 한 줄로 적는다. 담당 에이전트를 정한다: 표시/시연=demo-qa,
  수치=number-auditor, 규제=regulation-defender, 대본=pitch-scriptwriter, 윤문=korean-stylist.

  [3. 실행] 정한 에이전트에 Task로 위임하거나 직접 구현. 동결구역 회피. 검증: 프론트 npx vite build,
  백엔드 pytest. 통과해야 다음으로.

  [4. 감독 점검] [0]의 4개 체크리스트를 돌린다. 수치를 만졌으면 number-auditor 1패스, 대본이면 화법
  점검. 통과 못 하면 폐기하고 사유 기록.

  [5. 마무리·정지] 통과분만 커밋·푸시(claude/finals-prototype-prep-02e3b6). PROGRESS_LOG 맨 위에
  '사이클 브리핑' 3줄: 한 일 / 통과·실패 / 다음 사이클 제안. 노션 MCP가 붙어 있으면 '새벽 브리핑 로그'에
  한 행 추가하고 스프린트 보드 카드를 진행중·완료·보류로 이동(안 붙으면 생략 — 레포가 진실).
  그리고 정지하라. 할당량을 끝까지 쓰지 마라. 다음 사이클이 잇는다.

  [6. 하루 1회 풀 검증] PROGRESS_LOG로 오늘 아직 안 했다고 확인되면, 이 사이클에서 number-auditor·
  regulation-defender·demo-qa 3검증을 읽기전용 병렬로 한 번 돌리고 결과를 _workspace/에 남긴다.
  이미 오늘 했으면 생략하고 [2]의 일반 작업을 한다.
  ```
- **Model:** Claude Opus (claude-opus-4-8)
- **Repository:** `moon0825/majung`  (브랜치 푸시는 `claude/` 접두 → 본선 브랜치 그대로 허용)
- **Environment:** Default(Trusted) + **Setup script** 권장:
  ```bash
  cd backend && pip install -r requirements.txt || true
  cd ../frontend && npm install || true
  ```
- **Trigger → Schedule → 간격(Interval) = 90분(1시간 30분).** 앱이 분 단위 간격을 지원하면 90분, 아니면 **매시간(Hourly)** 으로. 종일 자리를 비울 때 90분마다 한 사이클씩 작은 덩어리를 전진시킨다. 각 사이클은 할당량을 끝까지 쓰지 않고 작게 끝낸 뒤 멈추므로, 할당량이 소진된 시간대의 사이클은 가볍게 넘어간다(자가 스로틀). "한 방에 5시간"이 아니라 "90분마다 한 조각, 종일"로 이해하면 된다.
- **Create.** 즉시 한 번 돌려보려면 **Run now**.

**방법 2 — CLI:** 터미널에서
```
/schedule 매일 새벽 2시에 마중 본선 백로그 진행
```
이후 세부(레포·환경·모델)는 walk-through 또는 웹에서 편집. (웹 세션 안에서는 `/schedule` 불가 — 웹 UI 사용.)

> 한계: 루틴은 **최소 주기 1시간**(그래서 90분 권장), 계정 **일일 실행 한도**·구독 사용량을 소모한다. 각 사이클이 작게 끝내므로 종일 돌려도 한 방에 다 태우지 않는다. 분 단위 간격이 안 되면 매시간으로 두고 사이클 프롬프트가 알아서 작게 처리한다.
> 시간대: 이 환경은 UTC. 웹/CLI는 입력한 로컬(KST) 시각을 알아서 변환하므로 **KST로 입력**하면 된다.

---

## B. 절대 규칙 (위반 시 즉시 중단)
- **동결 구역 수정 금지** (`NIGHTLY_BACKLOG.md` 상단 규칙과 동일): Gate A/B/C 순서·단일 실행 경로, lock/unlock·busyRef, 오프라인 폴백(healthRef 분기), paced 타이밍, suppressNotifs, api.js throw 금지 계약, 교차 고정 수치(FX 18.12/18.45, 대환 13.59%·연 246만, AML 컷 40/70).
- **main 직접 커밋·푸시 금지.** 작업은 **본선 브랜치 `claude/finals-prototype-prep-02e3b6`** 에서만. 머지는 사람이 아침에.
- 새 작업은 **표시 레이어·문서·테스트·발표자료 중심.** 송금 실행 경로 로직은 손대지 않는다.
- 일부 환경에서 파일 도구 편집이 잘린다. 기존 파일 편집은 셸 직접 쓰기(`cat > 파일`)로 하고 `wc -l`로 검증한다.
- 매 항목 후 빌드/테스트 통과를 반드시 확인. 실패하면 그 변경을 폐기하고 다음 항목으로.
- 7/3 이후 = **동결(freeze).** 코드 변경 금지, 문서 오탈자만.

## C. 한 사이클 절차 (90분, finals-orchestrator 지휘)
> 한 사이클 = 작고 완결된 한 덩어리. "최대한 많이"가 아니라 "하나를 제대로". 다음 사이클이 90분 뒤 잇는다.
1. `git fetch origin` → 본선 브랜치 체크아웃·최신화:
   `git checkout claude/finals-prototype-prep-02e3b6 2>/dev/null || git checkout -b claude/finals-prototype-prep-02e3b6 origin/claude/finals-prototype-prep-02e3b6` → `git pull origin claude/finals-prototype-prep-02e3b6`
2. **상태 파악.** PROGRESS_LOG 최근 5건으로 직전 사이클이 뭘 했는지 보고 중복을 피한다. 노션 보드(붙어 있으면)에서 `진행중` 카드 확인.
3. **이번 사이클 목표를 작게 잡는다.** 백로그 저위험 `- [ ]` 1~3개, 또는 큰 작업의 한 조각(예: 발표덱 v5 한 섹션만 `_workspace/`에 초안). **위험도 '중' 이상·`[!]`·`[!→리뷰]`는 건너뛴다.** 목표를 PROGRESS_LOG 맨 위 '사이클 계획' 한 줄로 적고 담당 에이전트를 정한다(표시/시연=demo-qa, 수치=number-auditor, 규제=regulation-defender, 대본=pitch-scriptwriter, 윤문=korean-stylist).
4. **실행.** 담당 에이전트에 Task 위임 또는 직접 구현. 동결 구역 회피, 셸 직접 쓰기.
5. **검증.** 프론트 `cd frontend && npx vite build --outDir /tmp/nightly-build --emptyOutDir`, 백엔드 `cd backend && pytest -q`(최소 20개 유지).
6. **감독 점검(드리프트 방지).** 커밋 전 4개 체크: ① 동결구역 안 건드렸나 ② 수치가 `docs/출처맵.md`와 일치하나(만졌으면 number-auditor 1패스) ③ 화법(`docs/화법_가이드.md`) 지켰나 ④ 빌드·테스트 그린인가. 하나라도 어긋나면 `git checkout -- .` 폐기 후 PROGRESS_LOG에 '실패·보류' 사유.
7. **마무리.** 통과분만 백로그 `- [ ]`→`- [x]`, 커밋 `git add -A && git commit -m "nightly: <요약>"`, 푸시 `git push -u origin claude/finals-prototype-prep-02e3b6`. PROGRESS_LOG 맨 위 '사이클 브리핑' 3줄(한 일/통과·실패/다음 사이클 제안). 노션 동기화(G, best-effort).
8. **정지.** 할당량을 끝까지 쓰지 말고 사이클을 끝낸다. 다음 사이클이 잇는다.
9. **하루 1회 풀 검증.** 오늘 아직 안 했으면(PROGRESS_LOG로 확인) 이 사이클을 풀 검증에 쓴다: number-auditor·regulation-defender·demo-qa를 읽기전용 병렬로 돌려 수치·규제·데모를 검증, 불일치를 pitch-scriptwriter가 `_workspace/`에 반영, korean-stylist가 윤문(최대 2회), number-auditor 1패스로 수치 회귀 확인. 리포트는 `_workspace/` 날짜별. 이미 했으면 일반 작업.

## D. 정지 조건 (사이클 단위)
- 한 사이클의 빌드/테스트 실패 → 그 변경 폐기하고 사이클 종료(다음 사이클이 다른 항목 시도).
- 남은 게 전부 `[!]`/위험'중' 이상 → 문서·발표 항목으로 전환, 없으면 사이클 스킵.
- 할당량 소진 시간대 → 사이클을 가볍게 넘긴다(자가 스로틀).
- 7/3 이후 동결 → 코드 변경 금지, 문서·오탈자만.

## E. 예산 (사이클 단위) — "작게, 자주, 끝까지 안 태운다"
- 한 사이클은 **저위험 1~3건 또는 큰 작업 한 조각**만. 할당량을 한 방에 소진하지 않는다 — 90분 뒤 다음 사이클이 잇는다.
- 사이클 끝에 반드시 '사이클 브리핑'을 먼저 확보(커밋)한 뒤 정지. 도중에 끊겨도 기록은 남게.
- 과도한 코드베이스 재탐색·라이브러리 추가·대규모 리팩터 금지. 큰 작업은 여러 사이클로 쪼갠다.
- 한 항목이 막히면 폐기하고 그 사이클은 종료 — 절대 동결 구역으로 우회하지 않는다.

## F. 아침 인수인계
- `PROGRESS_LOG.md` 최신 항목 = 사람이 가장 먼저 읽는 곳(노션이 안 붙었어도 여기엔 항상 있다).
- 노션 **JB AI 페이지**(아래 G) = 아침 대시보드. 밤새 쌓인 '사이클 계획'·'사이클 브리핑'·보드 카드 상태를 한눈에.
- 본선 브랜치 PR diff를 사람이 리뷰. 통과 못 한 시도는 커밋하지 않으므로 브랜치는 항상 그린.
- `[!→리뷰]`/위험'중' 항목(예: GET /metrics/loop)은 루틴이 손대지 않으니, 아침에 사람이 직접 구현·머지.

## G. 노션 대시보드 (best-effort — 레포 기록이 진실)
> 헤드리스 새벽 세션은 노션 MCP 인증이 안 붙을 수 있다. **기록의 진실은 항상 레포 파일**(PROGRESS_LOG·NIGHTLY_BACKLOG)이고, 노션은 그 위의 대시보드다. 노션이 붙으면 동기화하고, 안 붙으면 조용히 생략한다(절대 실패로 처리하지 않는다). 아침 세션(사람과 함께)에서 노션이 뒤처졌으면 그때 PROGRESS_LOG 기준으로 맞춘다.

- **JB AI 페이지:** https://app.notion.com/p/38ccba1f2f2581ee93b8c1d97bccfe98
- **마중 스프린트 보드** (data_source `8cb0eddd-0d3e-492c-9218-3064d004cd42`): 작업·상태(백로그/오늘밤/진행중/검증/완료/보류)·우선순위·레이어·위험도·담당에이전트·검증·메모.
  - 새벽 루틴: 처리 시작한 카드 → `진행중`, 검증 통과 → `완료`, 실패·되돌림 → `보류`(메모에 사유). 위험'중'·보류 카드는 옮기지 않는다.
- **새벽 브리핑 로그** (data_source `ccdaca1f-0e8e-4e78-a0e5-fd55b959c67c`): 날짜·한 일·통과·실패·사람이 볼 것·다음 제안. 매 사이클 한 행 추가(사이클 계획 1줄 + 브리핑 3줄).
- 노션 도구는 `ToolSearch`로 `mcp__Notion__notion-create-pages`(행 추가)·`notion-update-page`(카드 이동)를 그때 불러 쓴다. 스키마가 안 보이면 노션 미연동이니 생략.
