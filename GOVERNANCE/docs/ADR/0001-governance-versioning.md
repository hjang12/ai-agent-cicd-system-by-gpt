# ADR-0001: Governance 규칙의 버전 관리와 Source of Truth

## Status

Accepted — versioning principles remain active. The separate-repository topology in the original decision was superseded by ADR-0002 on 2026-09-18.

## Context

AI Coding Agent의 공통 운영 규칙이 Chat 또는 개별 프로젝트에만 존재하면 새 Agent가 과거 결정과 운영 경험을 안정적으로 복구하기 어렵다. 실제 운영 문제를 규칙에 반영하려면 Governance에도 추적 가능한 변경 이력이 필요하다.

## Decision

Governance는 버전·변경 이력·현재 상태가 추적 가능한 Repository 문서로 관리한다. 처음에는 별도 Repository를 사용했으나, ADR-0002의 monorepo 통합 이후 현재 경로는 다음과 같다.

- 공통 규칙: `GOVERNANCE/GOVERNANCE.md`
- 현재 버전의 단일 원본: `GOVERNANCE/VERSION`
- 변경 이력: `GOVERNANCE/CHANGELOG.md`
- 현재 Workspace 상태: `GOVERNANCE/docs/CURRENT_STATUS.md`
- 장기 이력: `GOVERNANCE/docs/DEVELOPMENT_HISTORY.md`

## Reason

- 프로젝트와 Chat을 넘어 동일한 운영 기준을 재사용할 수 있다.
- 규칙 변경을 검토·승인·검증하고 실제 운영 결과와 연결할 수 있다.
- 새 Agent가 공식 상태와 과거 의사결정을 구분할 수 있다.

## Consequences

- 시작 시 canonical Workspace와 Governance 경로를 확인한다.
- Governance 변경에는 버전·Changelog·관련 Context를 동기화한다.
- Repository topology는 ADR-0002 및 현재 저장소 구조를 기준으로 하며, 이 ADR의 이전 별도 Repository 설명을 현재 구조로 해석하지 않는다.

## Revisit Condition

- Governance 탐색·유지 비용이 과도해지는 경우
- 공통 규칙과 프로젝트별 예외의 경계가 불명확해지는 경우
- 운영 규칙 검증·승인·배포 구조를 바꿀 필요가 생기는 경우
