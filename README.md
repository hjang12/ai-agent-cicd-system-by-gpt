# AI Agent CI/CD System

AI Coding Agent를 활용한 소프트웨어 개발·검증·배포 운영 체계를 정의하고, 실제 프로젝트 경험을 통해 지속적으로 개선하기 위한 공통 운영 규칙 저장소입니다.

## 목적

이 저장소는 특정 프로젝트의 소스 코드를 관리하지 않습니다. 대신 AI Coding Agent가 요구사항 분석부터 개발, 검증, 배포, 운영, 문서화까지 수행하는 방식을 표준화하고 그 표준 자체의 변경 이력을 관리합니다.

핵심 원칙은 다음과 같습니다.

- 장기적인 유지보수성·확장성·검증 가능성·재현성을 우선합니다.
- GitHub를 공식 Source of Truth로 사용합니다.
- 코드가 아니라 실제 요구사항 충족과 검증 결과를 완료 기준으로 삼습니다.
- 위험한 변경에는 Human Approval을 적용합니다.
- 프로젝트 개발 경험을 바탕으로 운영 규칙 자체도 지속적으로 개선합니다.

## 문서 구조

```text
VERSION
CHANGELOG.md
GOVERNANCE.md

 docs/
 ├── CURRENT_STATUS.md
 ├── DEVELOPMENT_HISTORY.md
 ├── AGENT_HARNESS.md
 ├── VERIFICATION.md
 ├── EVIDENCE.md
 ├── TRACEABILITY.md
 └── ADR/

 templates/
 ├── CURRENT_STATUS.md
 ├── DEVELOPMENT_HISTORY.md
 ├── ADR.md
 └── CHANGE_RECORD.md
```

## 버전 관리

현재 운영 규칙의 기준 버전은 `1.0.0`입니다.

변경은 실제 프로젝트에서 발견된 문제, 개선 요구 또는 새로운 운영 경험을 근거로 기록합니다. 큰 구조적 변화는 Major, 호환 가능한 운영 방식의 개선은 Minor, 문서·오류 수정은 Patch로 구분합니다.

## 적용 방법

각 프로젝트는 이 저장소의 운영 규칙을 참고하여 자체 `CURRENT_STATUS.md`, `DEVELOPMENT_HISTORY.md`, `ARCHITECTURE.md`, `ADR/` 등의 프로젝트 지식 문서를 운영할 수 있습니다.

운영 규칙의 변경은 이 저장소에서 버전으로 관리하고, 변경 사유와 실제 적용 결과를 기록합니다.
