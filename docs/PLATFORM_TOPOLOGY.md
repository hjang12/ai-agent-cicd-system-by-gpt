# Platform Topology

이 문서는 AI Agent CI/CD Governance가 적용되는 프로젝트들의 GitHub Repository와 Render 배포 자산을 어떤 계층으로 관리할지 정의한다.

## 1. 상위 구조

GitHub와 Render는 서로 다른 역할을 가진다.

```text
GitHub Organization / Account Namespace
        ↓
GitHub Repository
        ↓
CI / Verification
        ↓
Render Workspace
        ↓
Render Project
        ↓
Environment
        ↓
Service
```

GitHub는 소스 코드, 테스트, 문서, 설정, CI/CD 정의 및 프로젝트 지식의 공식 Source of Truth이다.

Render는 애플리케이션을 실행하고 배포하는 운영 환경이다. 실행 환경의 실제 상태도 검증 대상이지만, 배포된 서비스 자체를 소스 코드의 원본으로 취급하지 않는다.

## 2. GitHub Repository topology

GitHub는 Repository를 다른 Repository의 하위 객체로 배치할 수 없으므로, 전체 개발 자산의 상위 경계는 Organization을 사용한다.

권장 구조:

```text
GitHub Organization
├── ai-agent-cicd-system
├── personal-ai-janggi-trainer
├── time-dashboard
└── personal-mcp-server
```

현재 개인 계정에 직접 존재하는 Repository를 Organization으로 이전하는 경우에도 Repository 내부의 Git history와 독립적인 CI/CD 수명주기를 유지한다.

`ai-agent-cicd-system`은 제품 소스 코드가 아니라 공통 Governance Repository이다. Project Repository는 Governance를 참조하고 프로젝트별 Context와 구현을 자체 Repository에서 관리한다.

Monorepo 전환은 단순한 정리 작업으로 수행하지 않는다. 여러 프로젝트의 수명주기, 배포 단위, 권한, CI/CD가 실제로 하나로 묶여야 하는 경우에만 별도 ADR을 만든 후 결정한다.

## 3. Project Repository minimum structure

가능한 모든 장기 프로젝트는 다음 문서 구조를 가진다.

```text
README.md
docs/
├── CURRENT_STATUS.md
├── DEVELOPMENT_HISTORY.md
├── ARCHITECTURE.md
├── PRODUCT_BRIEF.md
└── ADR/
```

프로젝트에 필요하면 다음을 추가한다.

```text
docs/
├── API.md
├── DEPLOYMENT.md
├── TESTING.md
├── EVIDENCE.md
└── evidence/
```

Repository 이름은 제품/서비스 목적을 표현하고, Render Service 이름도 가능한 한 동일하거나 명확히 매핑한다.

## 4. Render topology

Render에서는 하나의 Workspace를 전체 개인 개발 환경의 상위 경계로 사용하는 것을 기본으로 한다.

그 아래에 제품 단위 Project를 만들고, Project 안에서 Production/Staging 등의 Environment와 Service를 관리한다.

권장 구조:

```text
Render Workspace
├── Project: personal-ai-janggi-trainer
│   └── Production
│       └── Service: personal-ai-janggi-trainer
│
├── Project: time-dashboard
│   └── Production
│       └── Service: time-dashboard
│
└── Project: personal-mcp-server
    └── Production
        └── Service: personal-mcp-server
```

개발 또는 검증 환경이 실제로 필요할 경우:

```text
Project: product-x
├── Production
│   └── service
└── Staging
    └── service
```

동일 Repository를 가리키는 중복 Service를 만들지 않는다. 필요에 의한 중복은 Environment 또는 명시된 Service 역할로 설명하고 문서화한다.

## 5. Source-of-truth relationship

```text
Requirement
→ GitHub Change
→ CI / Verification
→ Render Deployment
→ Health Check
→ Smoke Test
→ Result / Evidence
```

Render의 설정이 GitHub의 Configuration과 다른 경우 원인을 기록하고 가능한 범위에서 GitHub 기반 선언적 설정으로 회귀한다.

Auto Deploy를 사용하는 서비스는 연결된 Repository와 Branch가 명확해야 한다.

## 6. Project inventory

정리 시점의 실제 자산은 별도의 inventory 문서에서 기록한다. 추정으로 서비스나 Repository를 삭제하지 않는다.

최소한 다음을 기록한다.

- Repository
- Owner / Organization
- Default Branch
- Runtime
- CI/CD
- Render Workspace
- Render Project
- Environment
- Service
- Service URL
- Auto Deploy
- Active / Retiring / Archived 상태
- 삭제 전 보존 대상

## 7. Retired project

사용하지 않는 프로젝트는 바로 삭제하지 않고 Retire 절차를 거친다.

```text
Active
→ Retiring
→ Dependency / Data / Domain 확인
→ Deployment 중단
→ Repository 보존 여부 결정
→ Render 자산 삭제
→ Repository 삭제 또는 Archive
→ History 기록
```

삭제가 필요한 경우 다음을 확인한 후 수행한다.

- 사용자 데이터 보존 필요 여부
- 데이터베이스 및 영속 스토리지
- Domain / DNS
- Environment Variables / Secrets
- 외부 OAuth/API/Webhook 연동
- CI/CD 연결
- 다른 서비스가 호출하는 URL
- 문서 및 개발 이력
- 마지막 정상 배포 및 검증 결과

삭제 완료 후에도 삭제 사실, 이유, 범위, 시점을 `DEVELOPMENT_HISTORY.md` 또는 Governance Evidence에 남긴다.

## 8. Naming

가능한 경우 다음 이름을 일관되게 사용한다.

```text
GitHub Repository: <product-name>
Render Project:    <product-name>
Render Service:    <product-name>[-<role>]
Environment:       Production / Staging / Development
```

역할 suffix가 있는 Service는 `api`, `worker`, `cron`, `web` 등 실제 역할이 명확할 때만 사용한다.

## 9. Migration rules

GitHub Repository를 Organization으로 이전하거나 Render Workspace/Project 구조를 변경하는 작업은 일반적인 코드 수정과 구분한다.

변경 전에 현재 상태를 기록하고, 변경 후 동일한 Repository/Branch/Environment/Service 연결과 배포 정상 여부를 검증한다.

플랫폼에서 직접 이전 기능을 제공하지 않아 재생성이 필요한 경우에는 다음을 명시적으로 비교한다.

```text
Old Resource
→ Configuration Capture
→ New Resource
→ Deployment
→ Verification
→ Traffic / Domain Cutover
→ Old Resource Retirement
```

기존 리소스 삭제는 새 리소스의 정상 동작이 확인된 후 수행한다.

## 10. Current cleanup target

2026-09-15 기준 확인된 Render 자산 중 `project-yeosamo`와 `project-yeosamo-app`은 동일 GitHub Repository를 가리키는 별도 Render Service이다.

사용자가 해당 프로젝트의 종료를 결정했으므로 현재 상태는 `Retiring`으로 취급한다.

이 저장소에서 플랫폼 정리 원칙은 확정하지만, Render 삭제와 GitHub Repository 삭제는 실제 리소스의 보존 대상과 외부 연결을 최종 확인한 후 수행한다.
