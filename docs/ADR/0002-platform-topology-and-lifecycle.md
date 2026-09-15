# ADR-0002: Repository 및 Deployment Topology 정리

## Status

Proposed for Governance v1.0.0 review

## Context

현재 GitHub에서는 Governance Repository와 개별 프로젝트 Repository가 모두 개인 계정의 동일한 레벨에 존재한다. GitHub Repository는 다른 Repository의 하위 객체가 될 수 없기 때문에 구조적 계층을 표현하기 어렵다.

현재 Render에는 하나의 Workspace 아래에 여러 서비스가 존재하며, 일부 서비스는 동일 GitHub Repository를 중복해서 가리키고 있다. 특히 `project-yeosamo`와 `project-yeosamo-app`은 동일 Repository를 대상으로 하는 별도 Render Service이다.

프로젝트가 늘어날수록 코드 구조뿐 아니라 Repository, CI/CD, 배포 환경, Service, 문서 및 Lifecycle의 관계를 명확하게 관리할 필요가 있다.

## AI Proposal

1. 모든 프로젝트를 하나의 GitHub Monorepo로 통합한다.
2. 개인 GitHub 계정을 유지하면서 Repository를 동일 계층으로 관리한다.
3. GitHub Organization을 상위 Namespace로 사용하고 Governance와 Project Repository를 형제 Repository로 관리한다.
4. Render는 하나의 Workspace를 상위 경계로 사용하고 제품별 Project → Environment → Service 구조를 사용한다.

## User Decision

Organization 기반의 3번 구조를 목표 구조로 채택한다. 여사모 프로젝트는 종료 대상으로 분류한다.

## Decision / Reason

### GitHub

```text
GitHub Organization
├── ai-agent-cicd-system
├── personal-ai-janggi-trainer
├── time-dashboard
└── personal-mcp-server
```

Governance는 Repository의 부모가 아니라 전체 Repository에 적용되는 공통 정책으로 동작한다. 각 Project Repository는 자체 코드, 테스트, Context, Architecture, History를 독립적으로 가진다.

Monorepo는 프로젝트 간 lifecycle과 CI/CD를 실제로 하나로 묶어야 하는 요구가 생길 때만 별도 ADR로 검토한다.

### Render

```text
Render Workspace
└── Project
    └── Environment
        └── Service
```

제품별 Project를 만들고 Production/Staging 등의 Environment를 분리한다. 동일 Repository를 가리키는 중복 Service는 명확한 역할이 없는 한 유지하지 않는다.

### Lifecycle

사용하지 않는 프로젝트는 즉시 삭제하지 않고 Retiring 단계에서 데이터, Domain, Secret, 외부 연동, CI/CD, 저장소 보존 여부를 확인한 후 삭제한다.

## Consequences

- GitHub Organization은 Repository 전체를 하나의 논리적 개발 생태계로 묶는다.
- Governance와 Product의 lifecycle은 분리된다.
- 새 프로젝트를 추가할 때 동일한 문서와 운영 기준을 적용하기 쉬워진다.
- Render의 중복 Service와 오래된 배포 자산을 식별하고 제거할 수 있다.
- Organization 이전과 Render 구조 변경은 운영 중단 가능성이 있으므로 사전 검증이 필요하다.

## Revisit Condition

- 프로젝트 규모가 커져 Organization 내부의 별도 Team/Namespace가 필요해지는 경우
- Monorepo가 실제로 더 적합한 CI/CD 및 lifecycle 모델이 되는 경우
- Render Workspace 또는 Project 구조가 현재 규모에 맞지 않게 되는 경우

## Evidence

2026-09-15 기준 GitHub Repository 목록과 Render Workspace/Service 목록을 직접 확인하여 `docs/PROJECT_INVENTORY.md`에 기록했다.
