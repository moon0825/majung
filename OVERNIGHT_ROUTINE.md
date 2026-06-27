# 새벽 자동 개발 루틴 (마중 / JB 본선)

> 매일 새벽 Anthropic 클라우드에서 자동 실행되는 Claude Code **Routine**이 그대로 따르는 작업 지침.
> 목적: 본선(7/4~5) 전까지 매일 새벽 백로그를 안전하게 여러 건 전진시킨다.
> "5시간 분량"을 아낌없이 쓰되, **매 항목 빌드/테스트 게이팅**으로 브랜치는 항상 그린으로 유지한다.

---

## A. 루틴 켜는 법 (사람이 1회만 — 약 2분)

새벽 자동 실행의 정답은 **Claude Code on the web의 Routines** 다. 노트북이 꺼져 있어도 클라우드에서 돈다.
(세션 안의 CronCreate는 컨테이너가 비활성 시 회수되어 밤새 실행이 안 되므로 부적합 — 반드시 Routine 사용.)

**방법 1 — 웹 UI (권장):** [claude.ai/code/routines](https://claude.ai/code/routines) → **New routine**
- **Name:** `마중 새벽 개발`
- **Prompt (그대로 붙여넣기):**
  ```
  이 저장소의 OVERNIGHT_ROUTINE.md를 읽고 거기 적힌 절차를 정확히 따라
  NIGHTLY_BACKLOG.md의 백로그를 본선 브랜치에서 안전하게 전진시켜라.
  동결 구역은 절대 건드리지 말고, 매 항목마다 vite build / pytest를 통과시켜라.
  ```
- **Model:** Claude Opus (claude-opus-4-8)
- **Repository:** `moon0825/majung`  (브랜치 푸시는 `claude/` 접두 → 본선 브랜치 그대로 허용)
- **Environment:** Default(Trusted) + **Setup script** 권장:
  ```bash
  cd backend && pip install -r requirements.txt || true
  cd ../frontend && npm install || true
  ```
- **Trigger → Schedule → Daily.** 시간은 **본인 로컬(KST) 기준 02:00**(또는 새벽 1~3시 사이) 입력 — 자동으로 UTC 변환됨.
- **Create.** 즉시 한 번 돌려보려면 **Run now**.

**방법 2 — CLI:** 터미널에서
```
/schedule 매일 새벽 2시에 마중 본선 백로그 진행
```
이후 세부(레포·환경·모델)는 walk-through 또는 웹에서 편집. (웹 세션 안에서는 `/schedule` 불가 — 웹 UI 사용.)

> 한계: 루틴은 **최소 주기 1시간**, 계정 **일일 실행 한도**·구독 사용량을 소모한다. 1박2일 본선 전까지 매일 1회면 충분.
> 시간대: 이 환경은 UTC. 웹/CLI는 입력한 로컬(KST) 시각을 알아서 변환하므로 **KST로 입력**하면 된다(KST 02:00 = UTC 17:00).

---

## B. 절대 규칙 (위반 시 즉시 중단)
- **동결 구역 수정 금지** (`NIGHTLY_BACKLOG.md` 상단 규칙과 동일): Gate A/B/C 순서·단일 실행 경로, lock/unlock·busyRef, 오프라인 폴백(healthRef 분기), paced 타이밍, suppressNotifs, api.js throw 금지 계약, 교차 고정 수치(FX 18.12/18.45, 대환 13.59%·연 246만, AML 컷 40/70).
- **main 직접 커밋·푸시 금지.** 작업은 **본선 브랜치 `claude/finals-prototype-prep-02e3b6`** 에서만. 머지는 사람이 아침에.
- 새 작업은 **표시 레이어·문서·테스트·발표자료 중심.** 송금 실행 경로 로직은 손대지 않는다.
- 일부 환경에서 파일 도구 편집이 잘린다. 기존 파일 편집은 셸 직접 쓰기(`cat > 파일`)로 하고 `wc -l`로 검증한다.
- 매 항목 후 빌드/테스트 통과를 반드시 확인. 실패하면 그 변경을 폐기하고 다음 항목으로.
- 7/3 이후 = **동결(freeze).** 코드 변경 금지, 문서 오탈자만.

## C. 매 실행 절차
1. `git fetch origin` → 본선 브랜치 체크아웃·최신화:
   `git checkout claude/finals-prototype-prep-02e3b6 2>/dev/null || git checkout -b claude/finals-prototype-prep-02e3b6 origin/claude/finals-prototype-prep-02e3b6` → `git pull origin claude/finals-prototype-prep-02e3b6`
2. `NIGHTLY_BACKLOG.md` 최상단의 미완료(`- [ ]`) 항목을 위에서부터 선택. **위험도 '중' 이상과 `[!]`(보류)·`[!→리뷰]`는 건너뛴다**(사람 리뷰 필요).
3. 구현. 동결 구역 회피, 셸 직접 쓰기.
4. 검증:
   - 프론트: `cd frontend && npx vite build --outDir /tmp/nightly-build --emptyOutDir` (통과해야 함)
   - 백엔드: `cd backend && pytest -q` (최소 20개 유지)
   - 하나라도 실패하면 `git checkout -- .` 로 되돌리고 그 항목은 PROGRESS_LOG에 '실패·보류'로 남긴다.
5. `PROGRESS_LOG.md` 맨 위에 한 줄 추가: 날짜 · 항목 · 결과 · 검증 · 다음 제안.
6. 백로그 항목 `- [ ]` → `- [x]`, 커밋: `git add -A && git commit -m "nightly: <항목 요약>"`
7. 푸시: `git push -u origin claude/finals-prototype-prep-02e3b6`
8. **정지 조건 전까지 2~7 반복** — 이 루틴은 1~2건이 아니라 **그날 처리 가능한 저위험 항목을 가능한 한 많이** 전진시킨다(아래 예산 참조).

## D. 정지 조건
- 빌드 또는 테스트가 **2회 연속** 실패
- 진행하려면 동결 구역을 건드려야 하는 항목만 남음(전부 `[!]`/위험'중'이상)
- 백로그 미완료(저위험) 항목 소진
- 컨텍스트·사용량 한도 근접 경고
- 7/3 이후 동결 상태

## E. 예산 (토큰·시간) — "5시간 분량, 아낌없이"
- 한 번의 새벽 실행에서 **저위험 항목을 연속으로 다수** 처리한다(상한 없음 — 빌드/테스트가 매번 통과하는 한 계속). 단 **위험도 '중' 이상은 건드리지 않는다**(사람 몫).
- 과도한 코드베이스 재탐색은 피하고, 라이브러리 추가·대규모 리팩터 금지.
- 큰 작업은 여러 밤으로 쪼갠다. 한 항목이 막히면 폐기하고 다음으로 — 절대 동결 구역으로 우회하지 않는다.

## F. 아침 인수인계
- `PROGRESS_LOG.md` 최신 항목 = 사람이 가장 먼저 읽는 곳.
- 본선 브랜치 PR diff를 사람이 리뷰. 통과 못 한 시도는 커밋하지 않으므로 브랜치는 항상 그린.
- `[!→리뷰]`/위험'중' 항목(예: GET /metrics/loop)은 루틴이 손대지 않으니, 아침에 사람이 직접 구현·머지.
