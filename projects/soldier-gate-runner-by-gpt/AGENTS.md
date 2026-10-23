# Gatefront Agent Instructions

- 공통 Governance: `../../GOVERNANCE/GOVERNANCE.md`.
- 시작 시 `AGENT_START.md`, `docs/CURRENT_STATUS.md`, 지정된 Task Checkpoint와 현재 CI 상태를 확인합니다.
- 목표는 한 판을 시작부터 승패까지 플레이할 수 있는 작은 웹앱을 완성하는 것입니다.
- 원본 Canvas 그림과 HTML/CSS/JavaScript만 사용합니다. 외부 게임 에셋, Last War 상표/이미지/코드, 외부 CDN, AI API, 서버 계정은 사용하지 않습니다.
- 핵심 흐름: 12명으로 시작 → 좌우 조작 → 덧셈/곱셈/퍼센트 게이트 선택 → 자동 사격과 적 웨이브 → 최종 보스 → 승리/패배 → 재시작.
- 앱스토어 패키징, 계정, 영구 성장/저장, 결제, 광고, 멀티플레이, 추가 레벨은 범위 밖입니다.
- 코드 변경 후 `node --check game.js`와 `python tests/browser_acceptance.py`를 실행합니다. CI의 실제 결과를 확인하기 전까지 통과했다고 기록하지 않습니다.
- Render 설정을 바꾸기 전에는 Workspace 선택과 기존 Blueprint를 확인합니다. 서비스 생성/배포와 Repository의 `render.yaml` 선언을 일치시킵니다.
- 필요 이상으로 구조를 일반화하거나 새 프레임워크를 추가하지 않습니다.
