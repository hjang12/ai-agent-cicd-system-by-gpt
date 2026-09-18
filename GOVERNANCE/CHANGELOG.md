# Changelog

이 문서는 AI Agent CI/CD System 운영 규칙의 버전별 변경 이력을 기록합니다.

## [1.0.0] - 2026-09-15

### Added

- AI Coding Agent 프로젝트 개발 및 운영의 기본 목적 정의
- 프로젝트 시작 시 환경·권한·코드·CI/CD·배포 상태를 우선 확인하는 절차 정의
- GitHub를 Source of Truth로 사용하는 원칙 정의
- Agent Harness 개념과 구성 요소 정의
- 모듈화·인터페이스 분리·교체 가능성을 우선하는 Architecture 원칙 정의
- 반복적인 변경과 자동 수정 루프를 전제로 한 개발 원칙 정의
- CI/CD를 Quality Gate로 활용하는 원칙 정의
- 검증 Evidence와 Traceability 관리 원칙 정의
- Reproducibility 요구사항 정의
- 변경 범위 최소화 원칙 정의
- Human Approval이 필요한 변경 유형 정의
- Version 및 외부 Dependency 관리 원칙 정의
- 최소 권한과 Production 보호 원칙 정의
- Deployment 및 Post-deployment Verification 원칙 정의
- Observability 원칙 정의
- 개발 과정에서 운영 규칙 자체를 지속적으로 개선하는 원칙 정의
- 프로젝트 지식 및 개발 이력 관리 원칙 정의
- 실패 및 복구 기록 원칙 정의
- Agent Context 복구 순서 정의
- 프로젝트별 예외 관리 원칙 정의
- Governance 자체의 변경 관리 원칙 정의
- 새 Agent 시작 시 긴 Governance 전문을 복사하지 않는 최소 시작 프롬프트 원칙 정의
- `AGENT_START.md` 추가
- `CURRENT_STATUS.md`를 빠른 Context 복구 문서로 명확히 정의
- GitHub Organization / Repository topology 원칙 정립
- Render Workspace / Project / Environment / Service topology 원칙 정립
- Project lifecycle의 Active / Maintenance / Retiring / Archived / Deleted 상태 정의
- Retiring 프로젝트 삭제 전 보존 대상과 외부 연결 확인 절차 정의
- `docs/PLATFORM_TOPOLOGY.md` 추가
- `docs/PROJECT_INVENTORY.md` 추가
- `docs/ADR/0002-platform-topology-and-lifecycle.md` 추가
- 플랫폼 정리 추적 Issue `#2` 기록

### Clarified

- 계획, AI 추론, 사용자 결정, 실제 구현, 실제 테스트 결과, 실제 배포 결과를 구분하도록 명시
- 코드 작성 완료와 실제 작업 완료를 구분하도록 명시
- 배포 성공과 서비스 정상 동작을 구분하도록 명시
- 기존 프로젝트 구조를 먼저 이해한 후 최소 변경하도록 명시
- Governance의 개선은 실제 프로젝트 경험을 근거로 수행하도록 명시
- Governance Repository는 Product Repository의 부모가 아니라 공통 정책 Repository이며, 상위 묶음이 필요할 경우 GitHub Organization을 사용한다.
- Render는 Source of Truth가 아니라 실행/배포 환경이며 GitHub → CI/Verification → Render → Post-deployment Verification 관계를 유지한다.
- 동일 Repository를 가리키는 중복 Render Service는 명확한 역할이 없으면 유지하지 않는다.
- 현재 여사모 자산은 삭제 완료가 아니라 `Retiring` 상태로 기록하며, 실제 삭제 여부는 플랫폼에서 확인한 뒤 기록한다.
- 현재 연결된 도구에서 직접 수행할 수 없는 Organization 생성/Repository 이전/Service 삭제 등의 작업은 실제 실행 없이 완료로 기록하지 않는다.
