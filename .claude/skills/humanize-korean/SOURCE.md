# 출처

이 스킬은 외부 공개 레포에서 그대로 가져왔다(vendored).

- 원본: https://github.com/epoko77-ai/im-not-ai  (경로 `.claude/skills/humanize-korean/`)
- 라이선스: MIT (`LICENSE.upstream` 참조)
- 가져온 날: 2026-06-27
- 버전: SKILL.md 기준 v1.5.0 (레포 전체는 Humanize KR v2.0 계열)

용도: AI(ChatGPT·Claude 등)가 쓴 한글 글에서 번역투·기계적 문체 등 AI 티를 탐지·윤문. 우리 `docs/화법_가이드.md`의 본격 버전이라 본선 발표 대본·문서 다듬기에 함께 쓴다.

> 파일 무결성: 설치 전 references/*.py를 스캔해 네트워크·subprocess·exec·파일삭제 없음을 확인(표준 라이브러리만 사용). 업데이트가 필요하면 원본 레포에서 다시 받아 같은 경로에 덮어쓴다.
