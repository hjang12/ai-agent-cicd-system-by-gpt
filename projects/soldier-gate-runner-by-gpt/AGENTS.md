# Gatefront Agent Instructions

- 공통 Governance: `../../GOVERNANCE/GOVERNANCE.md`.
- 시작 시 `AGENT_START.md`, `docs/CURRENT_STATUS.md`, 지정된 Task Checkpoint와 현재 CI 상태를 확인합니다.
- 목표는 한 판을 시작부터 승패까지 플레이할 수 있는 작은 웹앱을 완성하는 것입니다.
- 원본 Canvas 그림과 HTML/CSS/JavaScript만 사용합니다. 외부 게임 에셋, Last War 상표/이미지/코드, 외부 CDN, AI API, 서버 계정은 사용하지 않습니다.
- 핵심 흐름: 12명으로 시작 → 좌우 조작 → 수학 게이트 선택 → 세 구역을 통과하며 25개 이벤트 처리 → 적 유형별 전투와 사격 강화 패널 선택/파괴 → 최종 보스 → 승리/패배 → 재시작.
- 하나의 플레이 가능한 미션 안에서 콘텐츠를 확장합니다. 별도의 추가 레벨/캠페인, 영구 성장/저장, 계정, 결제, 광고, 멀티플레이, 앱스토어 패키징은 범위 밖입니다.
- 현재 콘텐츠 확장 목표: 세 구역(OUTER LINE / KILL ZONE / COMMANDER KEEP), 6종 적 전투 패턴, `+1` / `×2` / `+25%` 사격 강화 패널, 선택형 탱크 화력 보상. 수치 밸런스는 실플레이 후 조정합니다.
- 코드 변경 후 `node --check game.js`와 `python tests/browser_acceptance.py`를 실행합니다. CI의 실제 결과를 확인하기 전까지 통과했다고 기록하지 않습니다.
- Render 설정을 바꾸기 전에는 Workspace 선택과 기존 Blueprint를 확인합니다. 서비스 생성/배포와 Repository의 `render.yaml` 선언을 일치시킵니다.
- 필요 이상으로 구조를 일반화하거나 새 프레임워크를 추가하지 않습니다.

- 상단 툴바는 3레인/5레인 도로 모드, ×1/×2/×3/×4 속도 조절, RESET을 제공합니다. 레인 모드는 실행 중에는 변경할 수 없고 준비/결과 화면에서 선택합니다. 전용 가로모드/화면 회전 잠금 및 전체화면 기능을 추가하지 않습니다. HUD는 툴바의 실제 렌더링 높이를 기준으로 배치해 서로 겹치지 않게 합니다.
