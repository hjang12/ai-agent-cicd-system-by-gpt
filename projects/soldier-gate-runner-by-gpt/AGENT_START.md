# Gatefront — Agent Start

공통 운영 규칙은 저장소 루트의 `AGENT_START.md`, `AGENTS.md`, `GOVERNANCE/GOVERNANCE.md`를 따릅니다.

이 프로젝트는 외부 AI 모델 없이 동작하는 단일 라운드 2D 브라우저 게임입니다. 먼저 `AGENTS.md`, `docs/CURRENT_STATUS.md`, `docs/checkpoints/TASK-20261023-0003.md`를 읽고 현재 작업 범위와 검증 상태를 확인하세요.

핵심 구현은 `index.html`, `styles.css`, `game.js`입니다. 외부 이미지·폰트·라이브러리·API에 의존하지 않고 원본 Canvas 그래픽을 사용합니다. 현재 미션은 3개 구역·25개 이벤트로 구성됩니다. 상단 툴바는 ×1/×2/×3/×4 속도 조절과 RESET만 제공하며, 전용 가로모드/회전 잠금 및 전체화면 기능은 사용자 지시에 따라 범위에서 제외합니다. 화면 크기와 실제 방향에 따른 반응형 배치는 유지합니다. 콘텐츠 변경은 브라우저 회귀 테스트로 검증합니다.
