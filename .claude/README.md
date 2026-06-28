# .claude (운영 서브셋)

이 디렉토리는 마중 하네스의 **운영 계열만** 담는다. 클라우드 Claude Code가 이 레포를 클론해 실행(빌드·PR·설계문서) 작업을 할 때 쓰도록 공개한다.

포함(공개):
- 스킬: `jb-cloud-ops`(PR 검수·git/PR 위생·클라우드 핸드오프), `jb-demo-build`(데모 빌드·동결안전 확장), `jb-craft-standard`(완성도·em dash·다국어 품질), `jb-spec-design`(SRS·UX IA 형식), `fin-biz-tone`(어체)
- 에이전트: `jb-demo-engineer`, `jb-spec-architect`

제외(로컬 전용, `.gitignore` 처리):
- 전략·채점·적대 검증·오케스트레이션·학습은 공개하지 않는다. `jb-finals`, `jb-scoring-rubric`(지뢰·4부서), `jb-deck-strategy`, `jb-evidence-redteam`, `jb-research-redteam`, narrative/delivery/polish/scoring-qa 에이전트, `jb-learnings.md`는 로컬에만 둔다.

이유: 본선 심사 전에 내부 설득·지뢰·레드팀 플레이북이 공개 레포로 노출되면 안 된다. 오케스트레이션과 채점·검증 지능은 로컬 세션에서 돌리고, 클라우드는 실행만 맡는다.
