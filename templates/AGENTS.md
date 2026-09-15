# Agent instructions

공통 Governance: `hjang12/ai-agent-cicd-system`의 `GOVERNANCE.md`를 따른다.

작업 시작 전에 `AGENT_START.md`와 `docs/CURRENT_STATUS.md`를 확인하고, 현재 Repository의 코드·문서·CI/CD 상태를 실제로 확인한다. 실제 상태가 채팅 내용과 다르면 Repository를 우선한다.

- 핵심 domain/source 파일과 책임 경계를 명확히 유지한다.
- UI/HTTP 계층에 domain 규칙을 중복 구현하지 않는다.
- 최소 변경을 우선한다.
- 변경 후 프로젝트에 맞는 compile/build/test 검증을 실행한다.
- 외부 dependency를 추가할 때 필요성, 라이선스, 운영 영향을 검토한다.
- 배포 설정을 임의로 변경하지 않는다.
- 중요한 설계 결정, 반복되는 문제 해결, 운영 변경이 다음 Agent에 필요하면 관련 Context 문서를 갱신한다.
- 불확실한 동작은 추측하지 말고 실제 코드와 검증 결과를 확인한다.
