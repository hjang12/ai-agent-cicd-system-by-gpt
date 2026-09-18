# Agent instructions

공통 Governance: `../../GOVERNANCE/GOVERNANCE.md`를 따른다.

작업 시작 전에 `AGENT_START.md`와 `docs/CURRENT_STATUS.md`를 먼저 확인하고, 이어서 현재 Repository의 코드, 문서, CI 상태를 실제로 확인한다. 채팅 내용과 실제 상태가 다르면 Repository를 우선한다.

- Janggi 규칙과 legality는 `janggi/core.py`를 기준으로 한다.
- match lifecycle은 `janggi/match.py`를 기준으로 한다.
- engine/search/analysis/coaching 계층의 경계를 유지한다.
- HTTP/browser 계층에서 도메인 규칙을 중복 구현하지 않는다.
- 변경은 최소 범위로 하고 기존 테스트를 우선 보존한다.
- 코드 변경 후 `python -m compileall janggi tests tools`와 `python -m unittest discover -s tests -v`를 실행한다.
- Render 운영 설정을 코드와 문서에서 임의로 변경하지 않는다.
- 중요한 설계 결정, 반복되는 문제 해결, 배포/운영 변경이 다음 Agent에 필요하면 관련 Context 문서를 갱신한다.
- 불확실한 부분은 추측하지 말고 실제 구현/테스트 결과를 확인한다.
