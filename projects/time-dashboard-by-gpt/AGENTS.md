# Agent instructions

공통 Governance: `../../GOVERNANCE/GOVERNANCE.md`를 따른다.

작업 시작 전에 `AGENT_START.md`와 `docs/CURRENT_STATUS.md`를 먼저 확인하고, 이어서 현재 Repository의 코드, 문서, CI 상태를 실제로 확인한다. 실제 상태가 채팅 내용과 다르면 Repository를 우선한다.

- 핵심 서버 구현은 `timefolio_server.py`를 기준으로 한다.
- 외부 TimeETF 데이터 파싱 규칙을 변경할 때 기존 parser 테스트를 함께 수정한다.
- 웹 UI와 데이터 수집/파싱 로직의 역할을 불필요하게 결합하지 않는다.
- 최소 변경을 우선하고 외부 의존성을 추가할 때 필요성과 라이선스를 검토한다.
- 변경 후 `python -m py_compile timefolio_server.py`와 `python -m unittest discover -s tests -p 'test_*.py'`를 실행한다.
- Render는 `main` 자동 배포이며 검증 없이 배포 설정을 임의 변경하지 않는다.
- 중요한 설계 결정, 반복되는 문제 해결, 배포/운영 변경이 다음 Agent에 필요하면 관련 Context 문서를 갱신한다.
- 불확실한 동작은 추측하지 말고 코드와 테스트 결과를 확인한다.
