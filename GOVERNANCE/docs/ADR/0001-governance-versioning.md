# ADR-0001: Governance 규칙의 독립 저장소 및 버전 관리

## Status

Accepted for Governance v1.0.0

## Context

AI Coding Agent 운영 규칙이 개별 프로젝트 또는 ChatGPT 대화에만 존재하면 새 Agent가 과거의 결정과 운영 경험을 안정적으로 복구하기 어렵다. 또한 실제 프로젝트를 진행하면서 발견되는 운영상의 문제를 규칙 자체에 반영하려면 규칙에도 독립적인 변경 이력이 필요하다.

## Decision

AI Coding Agent의 공통 개발·운영 규칙을 `ai-agent-cicd-system` GitHub Repository에서 독립적으로 관리한다.

공식 Governance 문서는 `GOVERNANCE.md`, 현재 버전은 `VERSION`, 변경 이력은 `CHANGELOG.md`, 현재 상태는 `docs/CURRENT_STATUS.md`, 장기 개발 이력은 `docs/DEVELOPMENT_HISTORY.md`에서 관리한다.

## Reason

- 프로젝트 코드와 운영 규칙의 수명주기를 분리할 수 있다.
- 새로운 프로젝트와 새로운 Agent가 동일한 기준선을 참조할 수 있다.
- 운영 규칙 자체도 코드와 유사하게 변경·검증·승인·배포의 대상으로 관리할 수 있다.
- 실제 개발 경험을 Governance 개선으로 연결할 수 있다.

## Consequences

- 프로젝트를 시작하거나 이어받을 때 Governance Repository를 함께 확인해야 한다.
- 운영 규칙 변경은 Version과 Changelog를 갱신해야 한다.
- 실제 프로젝트의 적용 결과와 Governance 변경의 연결 관계를 기록해야 한다.

## Revisit Condition

- Governance Repository의 규모가 커져 문서 탐색 비용이 과도하게 증가하는 경우
- 프로젝트별 규칙과 공통 규칙의 경계가 불명확해지는 경우
- 자동화된 정책 검증 또는 배포 체계가 별도의 구조를 요구하는 경우
