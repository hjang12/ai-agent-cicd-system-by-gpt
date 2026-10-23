# Gatefront — Agent Start

공통 운영 규칙은 저장소 루트의 `AGENT_START.md`, `AGENTS.md`, `GOVERNANCE/GOVERNANCE.md`를 따릅니다.

이 프로젝트는 외부 AI 모델 없이 동작하는 단일 라운드 2D 브라우저 게임입니다. 먼저 `AGENTS.md`, `docs/CURRENT_STATUS.md`, `docs/checkpoints/TASK-20261023-0003.md`를 읽고 현재 작업 범위와 검증 상태를 확인하세요.

핵심 구현은 `index.html`, `styles.css`, `game.js`입니다. 외부 이미지·폰트·라이브러리·API에 의존하지 않고 원본 Canvas 그래픽을 사용합니다. 범위를 넓히기 전에 사용자가 승인한 한 판의 플레이와 실제 브라우저 검증을 우선하세요.
