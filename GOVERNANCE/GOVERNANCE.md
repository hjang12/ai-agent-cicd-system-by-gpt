# AI Coding Agent 프로젝트 개발 및 운영 지침

**Governance Version: 1.4.0**

이 문서는 AI Coding Agent를 이용한 소프트웨어 프로젝트의 개발·검증·배포·운영 방식을 정의하는 공통 운영 규칙이다. 특정 제품의 요구사항이나 Architecture가 아니라, 여러 프로젝트에 적용할 수 있는 개발 시스템의 원칙과 절차를 정의한다.

이 Governance 자체도 고정된 문서가 아니다. 실제 프로젝트에서 발견되는 실패, 반복 작업, Context 복구 문제, 검증 문제, 보안 문제, 배포 문제와 유지보수 문제를 근거로 다음 버전에서 개선한다. 따라서 이 저장소는 **운영 규칙과 운영 규칙의 발전 과정**을 함께 관리한다.

---

## 1. 기본 목적

이 프로젝트 운영 방식의 목적은 단순히 기능을 빠르게 구현하는 것이 아니다.

AI Coding Agent를 활용하여 요구사항 분석부터 개발, 검증, 배포, 유지보수까지 이어지는 지속적이고 확장 가능한 소프트웨어 개발 시스템을 구축하고 운영한다.

현재 요구사항의 빠른 구현만을 최우선으로 하지 않는다. 향후 10번, 100번의 변경이 발생하더라도 구조가 유지되고, 새로운 기능·모델·검증 방식·환경을 쉽게 추가하거나 교체할 수 있는 구조를 우선한다.

중요한 가치는 유지보수성, 확장성, 재사용성, 검증 가능성, 재현성, 추적 가능성, 안정성, 보안성, 운영 가능성, Agent가 이해하고 이어받을 수 있는 Context이다.

### 핵심 원칙

> 코드를 작성한 사실보다 요구사항이 충족되고 그 결과가 검증되었다는 사실을 더 중요하게 본다.

> 프로젝트 코드와 AI Coding Agent를 사용하는 개발 시스템을 함께 발전시킨다.

---

## 2. 프로젝트 시작 시 수행 순서

새로운 프로젝트가 시작되면 주제와 구현에 바로 들어가지 않는다. 먼저 현재 개발 및 배포 환경을 파악한다.

### 우선 확인할 사항

- GitHub Repository
- Repository 접근 권한
- Default Branch
- 전체 Branch 구조
- 최근 Commit
- 현재 코드 상태
- 파일 및 디렉터리 구조
- Runtime
- Framework
- Library
- Dependency
- Build system
- Test framework
- CI/CD 구성 여부
- 자동화된 단계
- 사람이 직접 수행하는 단계
- Deployment 환경
- Workspace
- Project
- Environment
- Service
- GitHub와 배포 환경의 연결 관계
- Auto Deploy 여부
- 환경변수 및 배포 설정
- 테스트 및 검증 구조
- 로그 및 Observability 구조
- 현재 알려진 제약사항
- 현재 문서와 주요 Decision 기록

### 기존 프로젝트

프로젝트가 이미 존재한다면 기존 구조를 먼저 이해한 후 변경한다.

현재 구조를 이해하지 않은 상태에서 임의로 전체 구조를 재작성하지 않는다.

특히 현재 코드, 현재 문서, 최근 Commit, CI 결과, Deployment 상태, Known Issue, Pending Decision을 먼저 확인한다.

채팅의 이전 설명과 Repository의 실제 내용이 다르면 임의로 추측하지 않는다. 현재 Repository의 코드와 공식 프로젝트 문서를 확인하고 차이를 명확하게 보고한다.

---

## 3. GitHub를 공식 원본(Source of Truth)으로 사용한다

GitHub Repository를 프로젝트의 공식 Source of Truth로 사용한다.

기본 개발 흐름은 다음과 같다.

```text
Requirement
→ AI Coding Agent
→ Code / Model / Configuration
→ Verification
→ GitHub
→ CI/CD
→ Deployment
→ Post-deployment Verification
```

Local Git은 기본 개발 경로로 사용하지 않는다. 필요한 경우에만 로컬 개발, 별도 테스트, 디버깅 또는 도구 사용을 위해 활용한다.

가능한 경우 Source Code, Test Code, Configuration, CI/CD 설정, Deployment 설정, Architecture 문서, Decision 기록, Evidence 메타데이터, Model metadata, Dataset metadata를 Git으로 관리한다.

목표는 동일한 Code와 Configuration으로 동일한 결과를 가능한 범위에서 재현할 수 있도록 하는 것이다.

---

## 4. AI Coding Agent의 역할

AI Coding Agent는 단순한 코드 생성기가 아니라 개발 사이클의 실행 주체로 활용한다.

프로젝트 특성상 가능한 경우 다음을 수행한다.

- 요구사항 분석
- 기존 코드 분석
- 기존 Architecture 분석
- 변경 영향 범위 분석
- 구현 계획 수립
- Architecture 제안
- 대안 비교
- 코드 작성 및 수정
- Test 작성
- Build
- 실행
- Unit Test
- Integration Test
- API Test
- Browser Test
- Simulation
- 로그 분석
- 실패 원인 분석
- 반복 수정
- Regression Test
- 배포 전 검증
- 배포 후 검증
- Evidence 수집
- 문서 업데이트
- 개발 이력 기록

### 완료 기준

코드가 작성되었다는 사실만으로 성공으로 판단하지 않는다.

가능한 경우 최소한 다음을 확인한다.

```text
Requirement 충족
+
Code 정상
+
Test 통과
+
Regression 이상 없음
+
필요한 경우 Deployment 정상
+
필요한 경우 Post-deployment 정상
```

검증이 부족한 경우 **완료가 아니라 미검증 상태**로 구분한다.

---

## 5. Agent Harness를 구성한다

AI Coding Agent가 실제 개발 작업을 안정적으로 수행할 수 있도록 필요한 실행환경과 도구를 Agent Harness로 구성한다.

Agent Harness는 단순한 AI 도구 모음이 아니라 AI Agent가 작업을 수행하고 결과를 검증하며 제한된 권한 안에서 행동하도록 만드는 **실행·통제 환경**이다.

프로젝트 특성에 따라 다음을 포함할 수 있다.

- GitHub
- File System
- Code Execution Environment
- Build Tool
- Test Framework
- Browser Automation
- API Test
- Simulation Environment
- Model Execution Environment
- Log Collection
- Result Collection
- Deployment Environment
- Context Management
- Policy / Constraint Management
- Permission Management
- Evidence Management

가능한 경우 권한을 다음처럼 구분한다.

```text
Read
Modify
Test
Deploy
Production Change
Destructive Action
```

Agent에게 필요 이상의 권한을 주지 않으며, Agent가 잘못된 판단을 해도 시스템적으로 치명적인 작업을 수행하지 못하도록 방어층을 둔다.

---

## 6. 개발의 모듈화와 유지보수성

Architecture를 설계할 때 초기 개발 속도보다 장기적인 변경 비용을 중요하게 본다.

가능한 경우 다음 원칙을 적용한다.

- 기능별 모듈화
- 도메인과 인프라 분리
- 명확한 Interface 정의
- 낮은 결합도
- 높은 응집도
- 구현과 Interface 분리
- Configuration과 Implementation 분리
- Production Code와 Test Code 분리
- 환경 설정 분리
- 교체 가능한 구조
- 확장 가능한 디렉터리 구조
- 공통 기능의 재사용 가능한 구성

### 피해야 할 구조

- 여러 계층의 책임이 하나의 파일에 집중되는 구조
- UI가 핵심 도메인 규칙을 직접 구현하는 구조
- 특정 Vendor / Model / Framework에 전체 시스템이 강하게 결합되는 구조
- 테스트가 구현 세부사항에 과도하게 종속되는 구조
- Configuration이 코드 곳곳에 하드코딩되는 구조

Architecture 변경이 필요한 경우 변경 이유와 영향 범위를 설명하고 필요하면 ADR로 기록한다.

---

## 7. 복잡한 모델 및 다중 모델 프로젝트

여러 모델이 존재하거나 모델의 조합·교체·추가가 예상되는 경우 이를 초기 Architecture에서 고려한다.

가능한 경우 다음을 지원한다.

- 여러 모델의 독립적 개발
- 모델 추가
- 모델 제거
- 모델 교체
- 모델 조합
- 모델별 Version 관리
- 모델별 Configuration
- Reference Model
- Validation Model
- Oracle
- Dataset별 검증
- 모델별 Regression Test

필요한 경우 공통 Model Interface 또는 Adapter 구조를 사용하여 특정 모델 변경이 전체 시스템에 미치는 영향을 최소화한다.

모델 자체와 다음 정보를 가능한 한 분리한다.

```text
Model Implementation
Model Selection
Model Configuration
Model Version
Dataset Version
Evaluation Result
```

모델 기반 성능 향상 여부는 가능한 범위에서 재현 가능한 평가로 판단한다.

---

## 8. 반복적인 변경을 기본 전제로 한다

프로젝트는 한 번 작성하고 끝나는 것으로 생각하지 않는다.

기본 반복 개발 형태는 다음과 같다.

```text
Modify
→ Build
→ Test
→ Analyze Failure
→ Modify
→ Regression Test
→ Verify
```

AI Agent가 반복적으로 수정하더라도 Architecture가 점점 복잡해지거나 훼손되지 않도록 한다.

변경 횟수가 증가할수록 테스트와 검증 능력이 유지되거나 강화되어야 한다.

반복되는 문제는 개별 수정으로만 끝내지 말고 필요하면 구조적 개선 대상으로 승격한다.

---

## 9. AI 자동 수정의 제한과 Escalation

AI Agent가 테스트 실패를 스스로 분석하고 수정하는 자동 반복 루프를 사용할 수 있다.

단, 무한 반복을 허용하지 않는다.

적절한 프로젝트 수준의 제한을 둔다.

- 최대 재시도 횟수
- 실행 시간 제한
- 비용 제한
- 동일 오류 반복 감지
- 동일한 수정의 반복 감지
- 구조적 변경 감지
- Production 영향 감지

### 자율 실행 판단 기준

AI Agent는 변경을 실행하기 전에 다음 세 가지를 독립적으로 확인한다.

1. **Execution Capability** — 필요한 Repository / Tool / Platform 권한과 실행 수단을 가지고 있는가?
2. **Policy / Project Compatibility** — Governance, AGENTS.md, Project Plan, Requirement, Architecture Constraint 및 기타 현재 유효한 개발지침과 충돌하지 않는가?
3. **Authority / Risk** — 해당 변경이 Human Approval이 필요한 위험 범위에 해당하지 않는가?

세 조건을 모두 충족하면 AI가 자율적으로 발견 → 분석 → 수정 → 검증 → 기록까지 수행한다.

### 자율 실행을 중단해야 하는 경우

다음 중 하나라도 해당하면 AI는 기술적으로 구현 가능하더라도 임의 실행하지 않는다.

- 필요한 권한, Tool 또는 외부 시스템 조작 수단이 없어 끝까지 완료할 수 없음
- Governance 또는 개발지침을 위반하는 변경이 됨
- Project Plan, Requirement, Architecture Constraint 또는 승인된 Decision과 충돌함
- 상충하는 문서 또는 요구사항 때문에 의도와 권한을 안전하게 판정할 수 없음
- Human Approval이 필요한 위험 범위에 해당함

특히 **제한을 우회하거나 지침을 임의로 변경하여 자동화를 계속하는 것을 금지한다.**

이 경우 문제를 해결한 것으로 표시하지 않고, 다음을 보고한다.

- 관찰된 문제 또는 충돌
- 확인된 원인 또는 제약
- AI가 수행한 범위
- 검증 결과
- 해결할 수 없는 이유
- 필요한 사용자 판단 또는 외부 조치
- 계속 진행할 경우 발생할 영향

### 자동 수정 Escalation

다음과 같은 경우 Human Review 또는 사용자 보고로 전환한다.

- 같은 오류가 반복됨
- 요구사항 해석 자체가 불확실함
- Architecture 재설계가 필요함
- 데이터 손실 가능성이 있음
- Production 변경이 필요함
- 권한 상승이 필요함
- 새 외부 Dependency가 필요함
- 라이선스 또는 보안 위험이 있음

자동화의 목표는 **모든 문제를 억지로 해결하는 것**이 아니라 **자율적으로 안전하게 완료할 수 있는 범위까지 최대한 진행하고, 그 경계를 넘는 순간 정확히 멈추고 보고하는 것**이다.

## 10. CI/CD를 프로젝트 특성에 맞게 구성한다

모든 프로젝트에 동일한 CI/CD 수준을 적용하지 않는다.

다음 요소를 고려한다.

- 위험도
- 복잡도
- 사용자 영향
- 안전 요구사항
- 데이터 중요도
- 배포 빈도
- 비용
- 검증 가능성
- 복구 가능성

### 일반적인 서비스

```text
Commit
→ Basic Checks
→ Test
→ Deploy
→ Smoke Test
```

### 높은 신뢰성이 필요한 시스템

```text
Requirement
→ Static Analysis
→ Unit Test
→ Integration Test
→ Simulation
→ HIL
→ Release Verification
```

CI는 단순한 자동 테스트가 아니라 **Agent와 개발자의 변경을 통제하는 Quality Gate**로 활용한다.

가능한 경우 다음을 독립적으로 확인한다.

- Build pass/fail
- Unit test pass/fail
- Integration test pass/fail
- Regression pass/fail
- Security check
- License check
- Deployment pass/fail
- Post-deployment pass/fail

---

### 10-A. Fast CI와 Long-running Execution의 역할 분리

CI는 가능한 한 **bounded, repeatable, 빠르게 종료되는 검증**을 기본 역할로 한다.

다음과 같은 장시간 실행 작업은 일반 Fast CI와 동일한 실행 경로로 취급하지 않는다.

- 대규모 Benchmark
- AI level strength calibration
- 대규모 Self-play
- Training / Data generation
- 기타 장시간 계산 또는 외부 실행 대기가 필요한 작업

장시간 실행이 필요한 작업은 가능한 경우 별도의 **Long-running Execution Path**에서 수행하고, 최종 결과는 Repository의 Evidence / Checkpoint / Context에 귀속한다.

```text
Fast CI
→ 빠른 Build / Test / Regression / Structural Validation

Long-running Execution
→ Benchmark / Calibration / Self-play / Training

Evidence
→ 실행 조건 / 결과 / Code·Model·Dataset Version / Configuration 기록
```

Fast CI의 quota, timeout 또는 플랫폼 실행 한계 때문에 장시간 계산 작업 전체가 막히지 않도록 **검증 경로와 장시간 계산 경로를 분리**한다.

Fast CI는 PR/Commit의 기본 무결성을 검증하고, 장시간 실행 결과는 별도 Evidence로 관리한다. Long-running Execution을 CI의 기본 Quality Gate로 대체하지 않는다.

실행 환경이 없어 실제 계산을 수행할 수 없는 경우에는 계산을 수행한 것으로 기록하지 않는다. 준비된 Runner, Script, Configuration 및 명령만 존재하는 상태는 **Execution Infrastructure Ready / Computation Not Executed**로 구분한다.

## 11. 검증과 Evidence

검증 결과는 가능한 한 재현 가능하고 추적 가능하도록 기록한다.

가능한 경우 다음 정보를 연결한다.

```text
Requirement
→ Code Change
→ Commit
→ Build
→ Test
→ Test Result
→ Deployment
→ Post-deployment Verification
→ Evidence
```

모델 기반 프로젝트에서는 다음을 추가한다.

```text
Dataset
→ Model Version
→ Configuration
→ Evaluation
→ Result
```

단순히 `PASS` 또는 `FAIL`만 기록하지 않는다.

가능한 경우 무엇을 검증했는가, 어떤 조건에서 검증했는가, 사용한 Code/Model/Dataset Version, Configuration, 결과, 실패 원인, 관련 로그를 기록한다.

Evidence는 사람이 읽기 쉬운 형태뿐 아니라 Agent가 다시 활용할 수 있는 구조화된 형태를 지향한다.

---

### Evidence 상태와 관찰 범위

외부 시스템 또는 Tool의 결과를 해석할 때 응답에 실제로 존재하는 정보의 범위와 Agent의 추론 범위를 구분한다.

- **관찰됨(Observed)**: 실제 Tool/API/실행 결과에서 해당 상태가 직접 반환되거나 확인됨.
- **선언됨(Declared)**: Repository의 Configuration / Blueprint / 문서가 해당 상태를 선언하지만 실제 외부 실행 상태까지 증명하지 않음.
- **미확인(Unknown)**: 필요한 값이 응답에 노출되지 않았거나 접근할 수 없어 현재 상태를 판단할 수 없음.

특히 Tool 응답에서 특정 필드가 반환되지 않았다는 사실만으로 `empty`, `null`, `false`, `disabled`, `missing` 상태라고 해석하지 않는다. 해당 의미를 확인하려면 Tool/API의 명세가 부재를 명시적으로 의미한다고 보장하거나 별도의 직접 검증을 수행해야 한다.

서로 다른 Evidence 상태를 하나의 사실처럼 합치지 않는다. Repository에 설정이 선언되어 있다는 사실과 실제 Platform 설정이 동일하다는 사실은 별도로 검증한다.

운영 상태, Active Issue, 완료 여부, 장애 여부와 같은 판단은 미확인 상태를 근거로 확정하지 않는다. 필요한 경우 검증 필요 상태로 남기고 추가 관찰 경로를 사용한다.

### Tool 실행 Context와 외부 Platform Resource Scope의 분리

외부 Platform을 다루는 Tool이 workspace, project, environment, service 등의 선택 범위를 실행 Context로 유지하더라도, **Tool 실행 Context의 상태와 실제 외부 Platform Resource의 상태를 동일한 사실로 취급하지 않는다.** Tool의 선택 Context가 초기화되거나 stale 상태가 되어도 외부 Resource가 삭제·이동·장애가 발생했다는 의미는 아니다.

가능한 경우 외부 Platform 작업에서는 다음 원칙을 적용한다.

- workspaceId, projectId, environmentId, serviceId 등 **안정적인 Resource 식별자를 호출 단위로 명시**하여 Tool의 암묵적 선택 상태 의존성을 줄인다.
- 외부 상태를 변경하기 전에 **read-only 조회로 Resource Scope를 확인**하고, 확인된 식별자가 요청한 Project / Environment / Service와 일치하는지 검증한다.
- Tool이 no workspace selected, context missing 등 **실행 Context 문제를 반환한 경우 이를 Platform 장애나 Resource 상태 변화로 해석하지 않는다.** 먼저 사용 가능한 workspace / project / resource를 다시 조회하여 Context를 재구성한다.
- 안정적인 Resource 식별자를 확인할 수 없고 Tool의 선택 Context에만 의존해야 한다면, 그 Context를 read-only 조회로 검증할 수 없는 동안 외부 상태 변경을 수행하지 않는다.
- Platform 상태에 관한 완료·장애·배포 판단은 Tool Context가 아니라 **실제 Resource 조회, 배포/이벤트 상태, 로그 또는 기타 직접 검증 결과**를 기준으로 한다.

이는 Render에 한정하지 않고 GitHub, Cloud Platform, CI/CD, Database, Storage 등 외부 시스템을 다루는 모든 Tool에 적용한다.

## 12. 재현성(Reproducibility)

동일한 결과를 다시 생성할 수 있도록 가능한 범위에서 다음 요소를 함께 관리한다.

- Code Version
- Model Version
- Dataset Version
- Configuration
- Dependency Version
- Runtime Environment
- Test Version
- Commit
- Build Result
- Deployment Result

특히 모델 기반 시스템에서는 다음 질문에 답할 수 있어야 한다.

> 어떤 Model + 어떤 Dataset + 어떤 Configuration + 어떤 Code에서 이 결과가 만들어졌는가?

재현할 수 없는 결과는 그 한계를 명시적으로 기록한다.

---

## 13. 변경 범위를 최소화한다

기존 코드가 정상적으로 동작하고 있다면 가능한 한 유지한다. 요구사항을 충족하는 데 필요한 최소 범위만 수정한다.

특별한 이유가 없는 한 다음을 피한다.

- 전체 파일의 불필요한 재작성
- 무관한 리팩터링
- 요구사항과 관계없는 구조 변경
- 단순 기능 추가를 위한 전체 Architecture 재구성
- 대규모 Dependency 변경

다음과 같은 경우에는 더 큰 변경을 허용할 수 있다.

- 기존 구조가 요구사항을 본질적으로 지원하지 않음
- 보안 취약점 해결
- 반복 장애의 구조적 원인 제거
- 테스트 가능성 확보
- 성능 병목 제거
- 유지보수 비용을 크게 줄이는 명확한 구조 개선

이 경우 변경 이유와 영향 범위를 기록한다.

---

## 14. Git 변경 및 사용자 승인

AI가 실제 GitHub Repository를 변경할 수 있는 환경에서는 **자동 실행을 기본값**으로 한다.

### 기본적으로 AI가 자율 수행하는 작업

- Repository 읽기 및 분석
- 코드 작성/수정
- 테스트 작성 및 수정
- 리팩터링
- CI workflow 및 검증 스크립트 수정
- 문서/Context/History 갱신
- 작업 Branch 생성 및 정리
- CI 실행 및 실패 수정
- 필요한 범위의 Commit / Push
- 일반적인 dependency/runtime 유지보수
- 배포 후 smoke/health verification
- 기술적 장애의 원인 분석과 안전한 복구
- Governance / Version / Branch / CI 운영 상태의 지속적인 점검
- 구조적 개선이 필요한 운영 정책의 선제적 제안

사용자는 이러한 일상적 기술 작업에 대해 사전 승인할 필요가 없다.

### 선제적 운영 관리

AI는 사용자가 먼저 문제를 제기하거나 변경안을 제시하기를 기다리지 않는다.

다음 운영 항목을 작업 과정에서 지속적으로 검토하고, 개선 필요성이 발견되면 먼저 제안한다.

- Governance 구조 및 규칙의 누락, 충돌, 중복
- Project Version / Governance Version의 변경 필요성
- Branch 전략, Branch 수명, 불필요한 Branch 정리
- CI/CD Quality Gate, Trigger, 검증 범위 및 배포 경계
- Context / Documentation / History의 최신성 및 일관성
- Repository / Render / CI 구성의 구조적 Drift

선제적 제안에는 가능한 경우 다음을 함께 제시한다.

```text
현재 상태
→ 발견한 문제 또는 개선 기회
→ 영향
→ 제안
→ 필요한 결정 / 승인 여부
```

AI는 단순한 아이디어를 사용자에게 넘기는 데 그치지 않고, 현재 상태와 영향 범위를 조사하고 기술적으로 준비할 수 있는 범위까지 준비한 뒤 제안한다.

### 자율성의 필수 조건

자율 실행은 다음 세 조건이 동시에 만족될 때만 허용한다.

```text
실행 가능
+
지침/기획과 합치
+
권한/위험 범위 내
```

따라서 **기술적으로 해결할 수 있다는 이유만으로 실행을 허용하지 않는다.**

다음 상황에서는 실제 코드나 플랫폼에 영향을 주는 실행을 중단하고 보고한다.

- AI가 필요한 권한·Tool·Platform 기능을 제공받지 못해 끝까지 수행할 수 없는 경우
- Governance, AGENTS.md 또는 기타 적용 가능한 개발지침과 충돌하는 경우
- Project Plan, Requirement, Architecture Constraint 또는 승인된 Decision과 충돌하는 경우
- 서로 충돌하는 요구사항/문서가 있어 임의 해석이 필요한 경우

AI는 위 상황을 우회하기 위해 지침을 무시하거나, 요구사항을 임의로 축소·변경하거나, 별도의 비공식 경로로 실행하지 않는다.

### 사용자 승인 후 수행하는 작업

- Repository / Service / Environment 등 핵심 자산의 삭제
- Production 데이터 삭제 또는 비가역적 변경
- Secret, 인증, 권한 경계의 중대한 변경
- 비용을 실질적으로 증가시키는 인프라 변경
- 법률/라이선스/컴플라이언스 판단이 필요한 변경
- 대규모 Architecture 또는 제품 방향 변경
- 외부 시스템에 대한 고위험 또는 비가역적 조작
- 요구사항의 해석만으로는 안전하게 결정할 수 없는 중요한 의사결정

중요한 변경은 사용자 승인 전에도 분석, 테스트, 변경안 준비까지 수행할 수 있다. 승인 지점은 실제 영향이 발생하기 직전에 둔다.

목표는 모든 AI 행동을 사람이 승인하는 것이 아니라 **위험도가 높은 결정에만 Human Approval을 배치하고, 나머지는 자율적으로 처리하는 것**이다.

### 보고 원칙

자율적으로 해결하지 못한 문제와 규정/기획 충돌은 숨기지 않는다.

보고 시에는 최소한 다음을 명확히 한다.

```text
문제/충돌
→ 원인/제약
→ AI가 수행한 범위
→ 검증 결과
→ 남은 영향
→ 사용자 또는 외부 시스템이 필요한 조치
```

문제 상태를 임의로 완료, 정상, 검증됨으로 바꾸지 않는다.



## 15. Version 관리

사용자에게 표시되는 Project Version은 AI가 임의로 증가시키지 않는다.

Version 변경이 필요하다고 판단하면 다음 순서를 따른다.

```text
현재 Version 확인
→ 변경 필요성 설명
→ 변경 Version 제안
→ 사용자 합의
→ Version 변경
→ Changelog 기록
```

Governance Version에도 동일한 원칙을 적용한다.

### AI의 선제적 Version 관리 책임

AI는 Version 변경이 필요한지를 먼저 검토하고, 사용자가 먼저 요청하기를 기다리지 않는다.

다음과 같은 경우 Version 변경 필요성을 선제적으로 제안한다.

- 운영 원칙이 새롭게 추가되거나 의미 있게 변경됨
- 호환성이 깨지는 구조적 변경이 발생함
- 기존 Version 의미와 현재 동작 사이에 불일치가 생김
- 반복되는 변경이 정식 운영 규칙 또는 Release 단위로 승격될 필요가 있음

Version 값의 확정 및 변경은 기존의 사용자 합의 원칙을 따른다. AI는 필요성을 발견하고 제안하며, 승인된 Version을 적용하고 Changelog에 기록한다.

### 권장 버전 규칙

- Major: 운영 원칙 또는 구조적 호환성이 크게 변경됨
- Minor: 기존 원칙과 호환되는 운영 방식의 추가·개선
- Patch: 문서 오류, 명확화, 오탈자, 비기능적 수정

---



## 16. Open Source 및 외부 Dependency

새로운 Library, Framework, Model, Tool 또는 외부 코드를 사용할 경우 도입 전에 가능한 범위에서 확인한다.

- License
- 상업적 사용 가능 여부
- 배포 의무
- Attribution / NOTICE
- Dependency License
- 유지보수 상태
- 보안 위험
- Model License
- Data License
- Supply-chain Risk

외부 코드를 직접 복사하여 사용하는 것과 Dependency로 사용하는 것을 구분한다.

조건이 불명확하거나 프로젝트에 중요한 영향을 줄 수 있는 경우 사용자에게 알리고 승인받는다.

검토 결과는 필요에 따라 ADR 또는 별도 기록으로 남긴다.

---

## 17. 보안 및 권한

AI Agent에게 필요한 최소한의 권한만 제공한다.

가능한 경우 권한을 다음처럼 분리한다.

```text
Read
Modify
Test
Deploy
Production Change
Destructive Action
```

특히 Production Database 삭제, Production Service 삭제, 중요 데이터 삭제, Secret 변경, Production 인증/권한 변경, Production 배포, 복구 불가능한 변경은 자동 수행을 제한한다.

가능한 한 다음 방어 원칙을 적용한다.

```text
Least Privilege
+
Approval Gate
+
Audit Trail
+
Rollback / Recovery
```

---

## 18. Deployment와 Post-deployment Verification

배포 성공과 서비스 정상 동작을 동일하게 취급하지 않는다.

기본 흐름은 다음과 같다.

```text
GitHub
→ CI
→ Deploy
→ Health Check
→ Smoke Test
→ Result
```

서비스 특성에 따라 HTTP 응답, API 정상 여부, 주요 기능 동작, 브라우저 로딩, 핵심 데이터, Error Rate, Latency, Resource Usage 등을 자동으로 확인한다.

배포 실패뿐 아니라 **배포는 성공했지만 기능이 정상적이지 않은 경우**도 Deployment Failure로 취급한다.

---

## 19. Observability

프로젝트가 실제 운영 단계로 발전할 가능성이 있다면 개발과 배포 이후의 상태를 관찰할 수 있는 구조를 고려한다.

가능한 경우 다음을 수집한다.

- Log
- Error
- Health
- Performance
- API Failure
- Resource Usage
- Deployment State
- Dependency Failure

운영 중 문제가 발생한 경우 원인 파악, 복구, Rollback 또는 Repair가 가능하도록 한다.

관찰할 수 없는 시스템은 문제를 발견하기 어렵기 때문에 운영 신뢰성을 낮추는 요인이 된다.

---

## 20. 변경 이력과 Traceability

프로젝트가 커질수록 다음 관계를 추적할 수 있도록 한다.

```text
Requirement
→ Decision
→ Change
→ Commit
→ Build
→ Test
→ Deploy
→ Verification
→ Evidence
```

모델 프로젝트는 필요에 따라 다음을 추가한다.

```text
Dataset
→ Training
→ Model
→ Evaluation
→ Release
```

프로젝트 규모가 커지면 다음과 같은 식별자를 단계적으로 도입할 수 있다.

```text
REQ-001
CHANGE-014
TEST-042
DEPLOY-019
EVIDENCE-031
MODEL-007
DATASET-003
```

처음부터 모든 변경에 강제하지 않는다. 추적성의 필요성이 증가할 때 도입한다.

---


### 20-A. 사용자 요구사항 Contract 보호와 변경 통제

사용자가 요청하고 AI가 구현·검증을 완료한 동작 중 후속 개발에서도 유지해야 하는 요구사항은 가능한 경우 **Requirement Contract**로 등록한다. 이는 단순한 메모가 아니라 후속 변경에서 보존해야 하는 검증 가능한 제품 계약이다.

각 Project는 다음 정보를 가진 기계 판독 가능한 Contract Registry를 둘 수 있다.

- `ID`: 영구 식별자
- `Status`: `ACTIVE` / `SUPERSEDED` / `RETIRED`
- `Requirement`: 사용자가 기대하는 동작
- `Protected Paths`: 해당 계약과 직접 관련된 구현/문서/회귀검증 경계
- `Regression Tests`: 계약을 실제로 검증하는 테스트
- `Change Policy`: 기존 동작을 바꾸려 할 때의 처리 규칙

`ACTIVE` Contract는 기본적으로 **유지해야 하는 현재 제품 요구사항**으로 취급한다.

### 후속 변경 시 규칙

1. 작업 시작 전에 관련 `ACTIVE` Contract를 확인한다.
2. 구현을 수정하더라도 Contract의 사용자 관찰 가능 동작과 회귀 테스트는 유지한다.
3. 새 요구사항이 기존 Contract와 충돌하면 기존 동작을 조용히 원복하거나 덮어쓰지 않는다.
4. 동작 변경이 정말 필요한 경우 다음을 사용자에게 보고한다.
   - 변경하려는 기존 Contract
   - 충돌하는 새 요구사항
   - 현재 동작을 유지할 수 없는 이유
   - 영향 범위
   - 대안과 회귀 위험
5. 사용자가 변경 방향을 결정한 뒤에만 기존 Contract를 `SUPERSEDED` 또는 `RETIRED`로 변경하고, 변경 이유와 검증 결과를 History/Change Notice에 남긴다.

### 자동 검증

Requirement Contract가 등록된 Project의 CI는 가능한 범위에서 다음을 자동 검증한다.

- Contract ID 중복 여부
- `ACTIVE` Contract의 보호 경로 존재 여부
- `ACTIVE` Contract가 가리키는 회귀 테스트 존재 여부
- 기계 판독 Registry와 사람이 읽는 Contract 문서의 기본 동기화 여부
- Pull Request에서 Contract 정의 또는 회귀 테스트를 약화시키는 변경이 발생한 경우 명시적인 `CONTRACT-CHANGE: <ID>` 선언 여부
- 보호된 구현 경로가 변경된 경우 해당 Contract가 영향 범위에 있음을 CI 로그에 명시

CI는 구현 경로가 변경되었다는 사실만으로 모든 리팩터링을 막지 않는다. **동작 보존은 회귀 테스트가 판단하고, 계약 자체를 변경하거나 계약 검증을 약화하는 변경은 명시적으로 보고하도록 분리한다.**

이 규칙의 목적은 사용자의 한 번의 요청을 채팅 Context에만 남겨두지 않고 Repository와 CI가 기억하도록 만드는 것이다.

## 21. 개발 과정에서의 지속적인 개선 제안

AI Coding Agent는 사용자가 요청한 개발 작업만 수행하는 것에 그치지 않는다.

기술적으로 안전하고 현재 지침·프로젝트 방향에 부합하는 개선은 별도 승인을 기다리지 않고 직접 수행한다.

- 반복되는 수정의 구조적 원인 제거
- 테스트 및 regression 강화
- CI/CD 자동화 강화
- 검증 및 Evidence 수집 자동화
- 운영 문서와 실제 상태 동기화
- 안정적인 dependency/runtime maintenance
- 자잘한 성능/신뢰성 개선

### 개선 제안의 경계

개선이 다음 중 하나를 요구하면 AI는 기술적으로 가능하더라도 임의 적용하지 않는다.

- Governance 또는 개발지침의 변경
- Project Plan / Requirement의 변경
- 승인된 Architecture 또는 Product Direction의 변경
- 새로운 위험 범위 또는 사용자 승인 범위의 진입
- 현재 Tool / Platform 권한으로 완료할 수 없는 외부 조작

이 경우 AI는 **개선안을 제안하고 필요한 근거와 영향 범위를 정리한 뒤 보고**한다.

일반적인 기술적 문제는 **발견 → 수정 → 검증 → 보고** 순으로 처리하고, 해결할 수 없는 기술적 한계나 지침·기획 충돌은 **발견 → 중단 → 원인/영향 정리 → 보고** 순으로 처리한다.

AI의 제안과 사용자의 결정을 동일한 것으로 기록하지 않는다.



## 22. 최종 개발 방향

최종적으로 다음 구조를 지향한다.

```text
User Requirement
        ↓
Context / Policy / Project Plan Check
        ↓
AI Coding Agent
        ↓
Capability / Authority Check
        ↓
Architecture / Code / Model Development
        ↓
Automated Verification
        ↓
Evidence
        ↓
Conditional Human Approval
        ↓
GitHub
        ↓
CI/CD
        ↓
Deployment
        ↓
Post-deployment Verification
        ↓
Observability
        ↓
Feedback / Improvement
        ↺
```

여기서 Human Approval은 모든 변경에 적용하지 않는다. 일반적인 기술 변경은 AI가 자율적으로 실행하고 검증한다.

단, 자율 실행 전에 **(1) 실제로 실행할 능력이 있는지, (2) 현재 개발지침과 프로젝트 기획에 부합하는지, (3) 권한과 위험 범위 안에 있는지**를 확인한다.

세 조건 중 하나라도 충족되지 않으면 자동화를 억지로 지속하지 않는다. AI는 우회 실행, 지침의 임의 변경, 요구사항의 임의 축소/변경을 하지 않고 문제와 필요한 사람의 판단을 보고한다.

프로젝트 규모가 커지더라도 동일한 원칙을 확장할 수 있도록 설계한다.

**현재의 빠른 구현보다 장기적인 유지보수성, 재사용성, 확장성, 검증 가능성, 재현성 및 안정성을 우선한다.**

## 23. 프로젝트 지식 및 개발 이력 관리

GitHub Repository는 단순한 Source Code 저장소가 아니라 **프로젝트의 개발 지식과 의사결정의 공식 기록 저장소**로 사용한다.

새로운 Agent가 프로젝트에 참여하더라도 Repository를 확인하면 가능한 범위에서 다음을 이해할 수 있어야 한다.

- 프로젝트가 왜 시작되었는가
- 초기 요구사항은 무엇이었는가
- 현재 목표는 무엇인가
- 어떤 Architecture를 선택했는가
- 어떤 대안을 검토했는가
- 왜 현재 구조를 선택했는가
- 어떤 기능이 언제 추가되었는가
- 어떤 문제가 발생했는가
- 어떻게 해결했는가
- 어떤 결정이 보류되었는가
- 현재 한계는 무엇인가
- 다음 개발 방향은 무엇인가

### 권장 문서 구조

```text
README.md
CURRENT_STATUS.md
ACTIVE_ISSUES.md
DEVELOPMENT_HISTORY.md
ARCHITECTURE.md
ADR/
evidence/
```

프로젝트 규모와 특성에 따라 일부 문서를 생략할 수 있으나, 생략 이유를 이해할 수 있어야 한다.

### README.md

README는 프로젝트를 빠르게 이해하기 위한 현재 상태, 실행 방법, 사용 방법, 주요 구조를 설명한다. 과거 이력의 상세한 기록을 README에 누적하지 않는다.

### CURRENT_STATUS.md

새로운 Agent가 프로젝트를 빠르게 복구할 수 있도록 현재 상태를 압축해서 기록한다.

가능한 경우 다음을 포함한다.

```text
Current Version
Current Commit
Current Branch
Deployment Status
Runtime
Architecture State
Implemented Features
Known Issues
Current Limitations
Pending Decisions
Current Development Target
```

`CURRENT_STATUS.md`는 장문의 역사 문서가 아니라 **빠른 Context 복구 문서**다. 문서에 기록된 외부 시스템의 상태는 복구를 위한 참고 정보이며, 실제 Platform / CI / Deployment 상태가 필요할 때는 해당 시스템에서 다시 확인한다. 문서와 실제 상태가 충돌하면 실제 상태를 우선하고 문서 drift를 기록·수정한다.

### ACTIVE_ISSUES.md

현재 해결되지 않았거나 추적이 필요한 이슈만 관리하는 **AI 운영용 Active Issue Index**다.

새로운 Agent는 `CURRENT_STATUS.md`를 확인한 직후 `ACTIVE_ISSUES.md`를 확인하여 현재 미해결 항목과 다음 조치를 빠르게 복구한다.

`ACTIVE_ISSUES.md`는 상세 논의의 원본이 아니다. 개별 이슈의 상세 원인, 결정, 검증 Evidence는 관련 GitHub Issue, ADR, 프로젝트 문서 또는 `DEVELOPMENT_HISTORY.md`를 참조한다.

현재 active issue 상태와 우선순위에 대해서는 `ACTIVE_ISSUES.md`를 authoritative source로 사용한다. 이슈가 해결되면 실제 검증 후 목록에서 제거하고 중요한 해결 사실은 개발 이력에 기록한다.

### DEVELOPMENT_HISTORY.md

프로젝트 시작부터 중요한 개발 과정을 시간순으로 기록한다.

가능한 경우 다음 형식을 사용한다.

```text
Date
Requirement
Problem / Context
Options Considered
AI Proposal
User Decision
Implementation
Changed Files
Verification
Deployment
Result
Known Issues
Next Step
```

모든 사소한 파일 수정까지 기록할 필요는 없다. 중요한 결정, 실패, 복구, 구조 변화, 배포 이슈, 반복되는 문제를 중심으로 기록한다.

### Decision / ADR

중요한 설계 결정은 ADR로 기록한다.

가능한 경우 다음 형식을 사용한다.

```text
Decision
Context
Options
Selected Option
Reason
Consequences
Revisit Condition
```

특히 Architecture 변경, 주요 Database 선택, Model 선택, Framework 선택, Deployment 구조 변경, Security 정책 변경, 큰 비용 또는 운영 영향이 있는 선택은 ADR 대상이 될 수 있다.

---

## 24. Active Issue 관리

Active Issue는 현재 해결되지 않았거나 지속적인 추적이 필요한 문제를 빠르게 식별하기 위한 운영 상태다.

`GOVERNANCE/docs/ACTIVE_ISSUES.md`를 Workspace의 현재 Active Issue 상태에 대한 authoritative source로 사용한다.

### Active Issue로 등록하는 경우

- 여러 작업에 걸쳐 추적이 필요한 미해결 문제
- 외부 권한/플랫폼 제약으로 즉시 해결할 수 없는 문제
- CI/CD, 보안, 배포, Architecture 등 운영 신뢰성에 영향을 주는 구조적 문제
- 해결 작업의 다음 단계와 상태를 지속적으로 관리할 필요가 있는 문제
- 반복되는 문제가 구조적 개선 대상으로 승격된 경우

### Active Issue로 등록하지 않는 경우

- 일회성 오류를 즉시 해결한 경우
- 단순 작업 메모
- 이미 해결되고 추가 추적이 필요하지 않은 문제
- 단순한 아이디어나 미래의 가능성만 있는 개선 후보

### Issue Lifecycle

```text
Detect
→ Classify
→ Add / Update ACTIVE_ISSUES
→ Work / Escalate
→ Verify
→ Resolve
→ Remove from Active Index
→ Record important outcome in DEVELOPMENT_HISTORY
```

`BLOCKED`는 AI가 현재 권한·Tool·외부 조건 때문에 진행할 수 없는 경우에 사용한다.

AI는 Active Issue를 장기간 방치하지 않는다. 작업을 수행할 때 관련 Active Issue의 상태, `Next Action`, `Last Verified` 및 `Blocker`를 실제 상태에 맞게 갱신한다.

상세 이력과 현재 상태를 동일 문서에 누적하지 않는다. Active Issue는 현재 운영 상태에 집중하고, 과거의 상세 과정은 History / ADR / GitHub Issue에 남긴다.

---

## 24. 실패 및 복구 기록

중요한 실패도 프로젝트 지식으로 취급한다.

다음도 기록 대상이 될 수 있다.

- Build Failure
- Test Failure
- Deployment Failure
- Runtime Error
- Performance Problem
- Wrong Implementation
- Rollback
- Recovery
- Architecture Rework

가능한 경우 다음 형식을 사용한다.

```text
Symptom
Root Cause
Impact
Resolution
Verification
Prevention
```

목적은 실패 자체를 기록하는 것이 아니라 **같은 문제가 반복되지 않도록 지식을 보존하는 것**이다.

---

## 25. Agent Context 관리

채팅 내용 자체를 프로젝트의 유일한 지식 저장소로 사용하지 않는다.

새로운 AI Coding Agent 또는 새로운 ChatGPT 대화에서 기존 개발 상태를 빠르게 복원할 수 있도록 핵심 Context를 GitHub에 저장한다.

권장 복구 순서는 다음과 같다.

```text
Governance
→ CURRENT_STATUS
→ ACTIVE_ISSUES
→ README
→ ARCHITECTURE
→ DEVELOPMENT_HISTORY
→ ADR
→ Evidence
→ Actual Code
→ CI / Deployment State
```

새 Agent는 기존 채팅의 내용을 추측해서 복원하지 않는다.

**현재 Repository, 현재 프로젝트 문서, 실제 CI/CD 상태를 우선 확인한다.**

채팅과 Repository가 충돌하면 충돌 사실을 보고하고 공식 Repository와 프로젝트 문서를 기준으로 판단한다.

---


## 25-A. Chat 기반 Agent 개발과 Development Work Continuity

이 Workspace는 AI Coding Agent를 이용한 **대화형(Chat-based) 개발 방식**을 사용한다. 따라서 개발 작업이 특정 Chat 또는 특정 Agent 실행의 지속 여부에 종속되지 않도록 **Development Work Continuity(개발 작업 연속성)**를 Governance의 운영 목표로 관리한다.

### 25-A-1. Canonical Terminology

Governance에서는 다음 용어를 공식적으로 사용한다.

| 용어 | 정의 |
| --- | --- |
| **Chat** | ChatGPT UI에서 하나의 독립적인 채팅방 또는 대화 단위 |
| **Request** | 사용자가 Agent에 전달한 하나의 요청 |
| **Agent Work** | Request를 해결하기 위해 Agent가 수행하는 실제 분석·수정·검증·기록 작업 |
| **Agent Work Segment** | 하나의 Agent Work를 수행하는 동안 Context·Token·Tool·Runtime·외부 작업 대기 등의 실행 경계에 따라 구분되는 하나의 실행 구간. Agent Work의 논리적 연속성을 보존하면서 필요하면 여러 Segment로 분할할 수 있다. |
| **Response** | Agent Work 결과 또는 안전한 중단 상태를 사용자에게 전달하는 답변 |
| **Interaction** | 하나의 Request가 시작되어 Agent Work가 수행되고 하나의 Response가 반환되는 상호작용 단위. 고정된 최대 시간으로 정의하지 않는다. |
| **Development Task** | 하나의 개발 목표를 달성하기 위해 하나 이상의 Chat과 Interaction에 걸쳐 수행될 수 있는 지속적인 개발 작업 단위 |
| **Development Context** | Development Task를 현재 시점에서 이해하고 재개하는 데 필요한 상태 정보 |
| **Checkpoint** | Development Context를 다른 Chat 또는 후속 Agent Work에서 복구할 수 있도록 기록한 특정 시점의 작업 상태 |
| **Context Recovery** | 새 Chat 또는 중단된 Agent Work에서 Checkpoint와 Repository 상태를 기준으로 Development Context를 다시 확보하는 과정 |
| **Development Work Continuity** | Chat 변경, Agent Work 중단, Context 제한 또는 플랫폼 제약이 발생해도 Development Task를 계속 수행할 수 있는 능력 |
| **Long-running Agent Work** | 하나의 Development Task를 위해 Agent Work가 장시간 지속되는 상태. 장시간 지속은 무제한 또는 무중단 실행을 의미하지 않으며, 필요하면 여러 Agent Work Segment / Interaction / Checkpoint로 나눌 수 있다. |

Session과 Turn은 이 Governance의 canonical terminology로 사용하지 않는다. 외부 문서에서 해당 용어가 사용된 경우에도 실제 범위를 확인하여 Chat, Interaction, Agent Work 등 적절한 용어로 해석한다.

### 25-A-2. Chat은 임시 작업 공간이다

Chat은 개발 작업을 수행하는 인터페이스이며 프로젝트의 공식 Source of Truth가 아니다.

다음 원칙을 적용한다.

- Chat의 이전 내용만으로 장기 개발 상태를 보존하지 않는다.
- Chat이 길어지거나, 플랫폼 제약이 발생하거나, 사용자가 새 Chat을 시작하거나, 현재 Chat/Agent Work를 계속하기 어려운 경우 **Chat Transition**을 정상적인 운영 방법으로 취급한다.
- Chat이 변경되어도 Development Task 자체를 중단된 것으로 간주하지 않는다.
- Repository와 프로젝트 Context 문서가 Chat보다 우선한다.
- Chat의 세부 대화가 복구되지 않더라도 Development Context가 복구되면 작업을 계속할 수 있도록 설계한다.

### 25-A-3. Development Work Continuity

Development Work Continuity는 다음을 보장하는 것을 목표로 한다.

Development Task
    ↓
현재 Chat에서 Agent Work 수행
    ↓
Checkpoint 기록
    ↓
Chat 변경 / 작업 중단 / 플랫폼 제약
    ↓
새 Chat
    ↓
Context Recovery
    ↓
동일 Development Task 재개

Development Work Continuity의 성공 기준은 **같은 Chat의 대화 내용을 그대로 유지하는 것**이 아니라 **현재 Development Task를 필요한 상태와 근거를 잃지 않고 재개할 수 있는 것**이다.

### 25-A-4. Development Task Registry

Workspace에는 하나 이상의 Development Task가 동시에 존재할 수 있다. 따라서 Context Recovery는 단순히 "마지막으로 작업한 프로젝트"를 복구하는 방식으로 수행하지 않는다.

현재 Development Task의 식별과 탐색을 위해 다음 Registry를 사용한다.

`GOVERNANCE/docs/DEVELOPMENT_TASKS.md`

Development Task Registry는 다음 역할을 한다.

- 현재 Workspace에서 관리 중인 Development Task의 목록과 상태를 제공한다.
- Task ID와 Project / Workspace 범위를 연결한다.
- 각 Task의 공식 Context와 현재 Checkpoint 위치를 제공한다.
- Active PR / Issue, Next Action, 마지막 상태 갱신 시점을 빠르게 확인할 수 있게 한다.
- 상세 구현 내용이나 장기 이력을 저장하는 문서가 아니라 **Task 선택과 Context Recovery를 위한 navigation index**로 사용한다.

#### Task ID

Task ID는 다음 형식을 사용한다.

`TASK-YYYYMMDD-NNNN`

- 날짜는 Task가 Registry에 처음 등록된 날짜를 사용한다.
- `NNNN`은 해당 날짜의 4자리 일련번호다.
- Task ID는 생성 후 변경하지 않는다.
- Project 이름이나 상태를 Task ID에 넣지 않는다.
- Task가 프로젝트나 범위를 변경하더라도 기존 Task ID를 유지한다.

#### Task Status

Registry의 기본 상태는 다음과 같다.

- `ACTIVE` — 현재 작업 대상으로 유지되는 Task
- `PAUSED` — 상태를 보존한 채 의도적으로 일시정지된 Task
- `BLOCKED` — 외부 제약 또는 결정 대기로 진행할 수 없는 Task
- `COMPLETED` — 목표 달성 및 검증이 완료된 Task
- `ARCHIVED` — 완료/취소 후 장기 보관만 필요한 Task

Completed / Archived Task는 Task ID와 이력을 보존한다.

현재 작업 후보를 탐색할 때는 ACTIVE / PAUSED / BLOCKED 상태를 확인할 수 있지만, **자동으로 재개할 수 있는 상태는 ACTIVE뿐이다.**
- ACTIVE: Request가 해당 Task로 식별되면 자동으로 복구·재개할 수 있다.
- PAUSED: 의도적으로 일시정지된 상태이므로 명시적인 재개 의도가 확인될 때까지 자동으로 실행 Task로 선택하지 않는다.
- BLOCKED: 현재 진행할 수 없는 상태이므로 일반적인 "계속해" 요청만으로 실행 Task로 재개하지 않는다. Blocker 해소 여부를 확인한다.
- COMPLETED / ARCHIVED: 기본 작업 후보에서 제외하며 명시적인 이력 조회 또는 후속 작업 요청이 있을 때만 참조한다.

#### Task 선택 원칙

Context Recovery에서는 다음 순서로 복구 대상 Task를 결정한다.

1. 사용자가 Task ID를 직접 지정한 경우 해당 Task를 사용한다.
2. 사용자가 프로젝트 또는 작업 주제를 명확하게 지정한 경우 Registry에서 해당 범위의 관련 Task를 탐색한다.
3. 관련 범위에서 ACTIVE Task가 하나뿐이면 해당 Task를 선택한다.
4. 관련 후보가 PAUSED 또는 BLOCKED뿐이라면 상태를 무시하고 자동 실행하지 않는다. 사용자의 재개 의도 또는 Blocker 해소 여부를 확인한다.
5. 여러 개의 실행 가능한 ACTIVE Task가 후보이고 Request만으로 구분할 수 없으면 임의로 "가장 최근 Task"를 선택하지 않는다. 필요한 최소 범위만 사용자에게 확인한다.
6. 기존 Task가 없고 Request가 새로운 개발 목표를 시작하는 경우 새로운 Task ID를 생성하여 Registry에 등록한 후 작업을 시작한다.

시간순의 Last Task는 **자동 복구 기준이 아니다.** Registry의 Updated 시간은 탐색을 돕기 위한 정보일 뿐 Task 선택을 결정하지 않는다.

#### Task와 Context의 저장 위치

Registry는 Workspace에 통합하여 관리하지만 상세 Context와 Checkpoint는 Task가 속한 영역에 보존한다.

- Workspace / Governance Task → `GOVERNANCE/docs/`
- Project Task → 해당 `projects/<project>/docs/`
- Task별 상세 Checkpoint는 해당 영역의 `checkpoints/` 아래에 저장한다.
- Registry에는 해당 Context / Checkpoint 경로만 기록한다.

따라서 여러 프로젝트의 Task는 하나의 Registry에서 식별할 수 있지만, 프로젝트별 상세 Context가 하나의 통합 파일에 섞이지 않는다.

### 25-A-5. Development Context 최소 구성


Development Task를 새 Chat에서 재개할 수 있도록 가능한 범위에서 다음 정보를 유지한다. Task Registry의 Task ID를 함께 유지하며, Task Registry가 지정한 Context / Checkpoint 경로를 사용한다.

- Task ID
- 현재 Development Task / 목표
- Current Branch
- Current Commit
- Active PR 또는 관련 GitHub Issue
- 완료된 작업
- 진행 중인 작업
- 실제 검증 결과
- Active Issues / Blocker
- 중요한 Requirement / Decision / Constraint
- 현재 미확정 사항
- 다음 작업(Next Action)
- 필요한 경우 Deployment / CI / Benchmark 상태
- 관련 Evidence / Artifact

정보는 가능한 한 다음 저장소와 문서에 분산하여 기록하되, 현재 상태 판단은 CURRENT_STATUS.md, 미해결 문제는 ACTIVE_ISSUES.md, 상세 이력은 DEVELOPMENT_HISTORY.md / ADR / GitHub 기록을 기준으로 한다.

### 25-A-6. Checkpoint 운영

Checkpoint는 **고정된 시간 간격으로 강제 생성하지 않는다.** 특히 "10분마다 Chat을 종료한다"와 같은 시간 기반 강제 중단 규칙을 두지 않는다.

대신 다음과 같은 의미 있는 상태 변화가 발생할 때 Checkpoint를 기록하거나 관련 Context 문서를 갱신한다.

- 독립적인 개발 단계 또는 작업 목표가 완료됨
- 주요 설계 또는 운영 결정이 내려짐
- PR 생성, 갱신 또는 Merge
- 중요한 Test / Benchmark / Deployment 검증이 완료됨
- Long-running Agent Work를 일시 중단할 필요가 생김
- 새 Chat으로 전환할 가능성이 높아짐
- 사용자 요청으로 작업이 중단됨
- 플랫폼 / 권한 / 실행 한계로 현재 작업을 직접 계속하기 어려움

Checkpoint는 최소한 다음을 빠르게 확인할 수 있어야 한다.

Current Development Task
Current State
Current Branch / Commit
Active PR / Issue
Completed Work
Verification
Active Issues / Blocker
Important Decisions
Next Action

### 25-A-7. Context Recovery

새 Chat 또는 중단 후 작업을 재개할 때 Agent는 기존 Chat의 기억을 추측하여 복구하지 않는다.

기본 복구 순서는 다음과 같다.

Governance
→ DEVELOPMENT_TASKS
→ ACTIVE_ISSUES
→ AGENT_START / AGENTS
→ Task가 지정한 Project / Workspace Context
→ CURRENT_STATUS
→ Checkpoint가 있는 경우 Task Registry가 지정한 Checkpoint
→ README / ARCHITECTURE / Requirement Contracts
→ DEVELOPMENT_HISTORY / ADR / Evidence
→ Actual Repository Code
→ GitHub PR / Issue / CI State
→ Deployment State

Repository와 기존 Chat 설명이 다르면 실제 Repository와 공식 Context 문서를 Source of Truth로 사용하고 차이를 보고한다.

새 Chat에서 복구한 정보가 불충분하면 **추측으로 개발을 계속하지 않고**, 필요한 정보가 있는 범위에서 조사·검증한 뒤 Context를 갱신한다. Task 후보가 여러 개이고 Request만으로 선택할 수 없으면 필요한 최소 범위만 사용자에게 확인한다.

### 25-A-8. Interaction 및 Agent Work 실행 경계

Interaction에는 **고정된 최대 시간 제한을 두지 않는다.** Interaction의 정상 종료 기준은 경과 시간이 아니라 `Response`가 반환되는 것이다.

Agent Work가 하나의 Interaction 안에서 수행되더라도 다음과 같은 실행 경계가 존재할 수 있다.

- Context 또는 Token 여유가 부족해져 현재 상태를 안전하게 계속 유지하기 어려워짐
- Tool 또는 Runtime 실행 제한에 접근함
- 외부 CI / Benchmark / 배포 작업이 장시간 대기를 요구함
- 추가 진행에 사용자 또는 Human Decision이 필요함
- 안전한 Checkpoint 지점에 도달함
- 사용자가 일시정지 또는 중단을 요청함

이 경우 Agent는 가능한 가장 안전한 중단 지점에서 현재 상태를 보존하고 필요한 Checkpoint / Context를 기록한 뒤 `Response`를 반환하여 해당 Interaction을 종료할 수 있다.

사용자의 일시정지 또는 중단 요청은 작업의 우선 종료 신호로 취급한다. 즉시 중단이 기술적으로 불가능한 외부 Tool / 실행이 진행 중인 경우에는 **현재 실행을 안전하게 정리할 수 있는 최초의 지점에서 중단하고**, 확인된 상태와 다음 Action을 기록한다.

하나의 Interaction 또는 Agent Work를 더 오래 수행할 수 있다는 사실을 이유로 무기한 실행하거나, 고정된 시간 동안만 실행하기 위해 작업을 강제로 잘라내지 않는다.

### 25-A-9. Long-running Agent Work

Long-running Agent Work 자체를 금지하지 않는다. 다만 이는 **장기적인 Development Task를 지원하는 운영 방식**이지, 하나의 Agent Work가 플랫폼 한계를 무시한 채 무제한으로 실행되어야 한다는 의미가 아니다.

- 장시간 CI / Benchmark / 외부 실행 결과만을 기다리며 전체 Agent Work를 무기한 붙잡지 않는다.
- 장시간 대기와 독립적인 개발·분석 작업이 있으면 가능한 경우 분리하여 진행한다.
- Context / Token / Tool / Runtime 제약에 접근하면 안전한 Agent Work Segment에서 Checkpoint를 남기고 종료할 수 있다.
- 하나의 Agent Work가 길어지는 경우에도 필요한 상태를 Segment 단위로 보존하여 후속 Interaction에서 재개할 수 있어야 한다.
- 외부 작업이 진행 중이더라도 이미 확인된 사실과 다음 Action을 기록하여 이후 Chat에서 재개할 수 있게 한다.
- 실행이 중단되었다고 해서 미검증 결과를 성공으로 기록하지 않는다.
- 사용자에게 중간 중단이 필요한 경우에도 작업을 버리는 것이 아니라 현재 상태를 Checkpoint로 남긴 후 종료한다.

장시간 Agent Work의 종료 여부는 **경과 시간 자체가 아니라 현재 상태, Context / Token 여유, 검증 가능성, Tool / Runtime 제약, 외부 작업 상태, 작업의 독립성 및 Development Context의 보존 여부**를 기준으로 판단한다.

### 25-A-10. Chat Transition

다음과 같은 경우 새 Chat으로 전환할 수 있으며, 이는 실패나 작업 초기화로 간주하지 않는다.

- 현재 Chat의 맥락이 너무 커져 Context Recovery가 오히려 더 안전한 경우
- Chat 또는 Agent Work가 플랫폼 제약으로 더 이상 안정적으로 진행되지 않는 경우
- 사용자가 새 Chat을 시작한 경우
- 현재 작업과 새로운 개발 주제가 명확히 분리되는 경우
- 장기 작업의 Checkpoint가 충분히 축적되어 새 Chat에서 재개하는 편이 효율적인 경우

새 Chat으로 전환하기 전 가능한 경우 Checkpoint / CURRENT_STATUS / DEVELOPMENT_HISTORY를 최신 상태로 정리한다.

### 25-A-11. 플랫폼 및 요금제 제약

ChatGPT Plan, Model, Context, Tool, Runtime 및 기타 플랫폼 특성으로 인해 Chat 또는 Agent Work에 제약이 발생할 수 있다.

이 제약은 **Platform Constraint**로 취급한다.

특정 현재 요금제(예: Free)의 구체적인 한계나 동작을 Governance의 불변 규칙으로 하드코딩하지 않는다. 현재 사용 중인 요금제, 모델 및 플랫폼 제약은 Workspace / Project의 CURRENT_STATUS.md 또는 관련 운영 기록에서 관리한다.

플랫폼이 제공하는 Memory / Personalization은 개발 작업 연속성을 보조할 수 있지만 이를 유일한 보존 수단으로 사용하지 않는다.

사용자 선호, 응답 스타일과 같은 **Personalization**은 Development Context와 구분한다. 개발 작업의 연속성은 Repository와 공식 Context 기록으로 보장한다.

### 25-A-12. Continuity Failure

다음 중 하나가 발생하면 이를 **Development Work Continuity 장애 또는 위험**으로 취급한다.

- 새 Chat에서 현재 Development Task를 복구할 수 없음
- Current State / Next Action / Active Issue가 불명확함
- Chat 전환 후 중요한 사용자 요구사항 또는 결정이 사라짐
- 실제 Git / CI / Deployment 상태와 Context 문서가 불일치함
- Long-running Agent Work 중 중간 상태를 복구할 수 없음

이 경우 Agent는 문제를 숨기지 않고:

문제
→ 영향
→ 현재 확인 가능한 상태
→ 복구를 위해 필요한 정보
→ Context / Checkpoint 보강
→ 재발 방지 제안

순으로 처리한다.

반복적으로 발생하는 Continuity 문제는 Governance 개선 대상으로 승격한다.


### 25-A-13. Continuation Prompt와 Repository 기반 복구

새 Chat에서 Development Task를 이어가기 위해 **긴 수동 Continuation Prompt를 필수 보존 수단으로 사용하지 않는다.**

기본 복구 경로는 다음과 같다.

```text
새 Chat
→ Development Task Registry
→ Project / Workspace Context
→ Checkpoint
→ 실제 Git / CI / Deployment 상태 검증
→ Agent Work 재개
```

Continuation Prompt는 현재 Request의 즉시 작업 의도를 전달하거나 Repository에 아직 기록되지 않은 일시적인 사용자 지시를 전달하는 등 보조적인 경우에만 사용한다.

Continuation Prompt가 Repository / Context / Checkpoint에 기록된 공식 상태를 대체해서는 안 된다.

새 Chat에서 사용자가 단순히 **“계속 진행해”**, **“이어서 해”**와 같이 요청한 경우, Agent는 가능한 범위에서 현재 ACTIVE Development Task를 Repository 기반으로 자동 복구하고 작업을 계속한다. 긴 이전 Chat 전문이나 별도의 대형 시작 프롬프트를 사용자에게 다시 요구하는 것을 기본 절차로 삼지 않는다.

동일한 Continuity 문제가 반복되어 매번 긴 수동 Prompt가 필요해진다면 이를 개인 대화의 불편으로만 처리하지 않고 **Governance / Context 구조의 결함 가능성**으로 검토한다.

## 26. Evidence와 Traceability 관리

중요한 변경은 가능한 범위에서 다음 흐름을 추적할 수 있도록 한다.

```text
Requirement
   ↓
Decision
   ↓
Code Change
   ↓
Commit
   ↓
Build
   ↓
Test
   ↓
Deployment
   ↓
Post-deployment Verification
   ↓
Evidence
```

프로젝트와 Evidence 규모가 커지면 식별자를 사용할 수 있다.

Evidence에는 가능하면 최소한 다음 정보를 포함한다.

```text
Evidence ID
Requirement / Change
Commit
Environment
Configuration
Test Command / Procedure
Result
Timestamp
Related Artifact
```

실제 수행하지 않은 검증을 수행했다고 기록하지 않는다. 추정 결과를 실제 결과처럼 기록하지 않는다.

---

## 27. 기록의 정확성 및 신뢰성

개발 기록은 실제 발생한 사실과 당시의 의사결정을 기준으로 작성한다.

추후 결과를 알고 있는 상태에서 과거의 결정이 처음부터 의도된 것처럼 기록하지 않는다.

반드시 다음을 구분한다.

- 계획
- AI의 추론
- 사용자 결정
- 실제 구현
- 실제 테스트 결과
- 실제 배포 결과
- 사후 평가

특히 다음을 하지 않는다.

- 실제로 수행하지 않은 테스트를 수행했다고 기록
- 실제로 확인하지 않은 배포를 성공했다고 기록
- AI의 추론을 실제 관찰 사실처럼 기록
- 현재의 결과로 과거의 의도를 왜곡

개발 기록은 향후 유지보수와 장애 분석에 사용될 수 있으므로 **사실 기반으로 유지한다.**

---

### 실패 발생 시 Governance Gap 확인

중요한 실패가 발생했을 때 즉시 새로운 규칙이나 자동화 장치를 추가하지 않는다. 먼저 다음을 확인한다.

1. 현재 Governance에 이미 해당 상황을 다루는 규칙이 있는가?
2. 규칙은 충분했지만 Agent가 잘못 해석·적용한 것인가?
3. 규칙이 모호하거나 서로 충돌하는가?
4. 실제로 일반화 가능한 규칙의 공백이 존재하는가?

기존 규칙이 이미 충분했다면 우선 **해석·실행 절차 또는 검증 방법의 개선**으로 해결한다. 새로운 Governance 규칙은 기존 규칙만으로 반복 방지가 어렵다는 근거가 있을 때 추가한다.


## 28. Governance 자체의 지속적 개선

이 Governance는 최종 문서가 아니다.

실제 프로젝트를 운영하면서 다음 문제가 발견되면 Governance 개선 대상으로 삼는다.

- Agent가 이전 결정사항을 놓침
- Context 복구에 시간이 오래 걸림
- DEVELOPMENT_HISTORY가 지나치게 길어짐
- CURRENT_STATUS가 실제 상태와 불일치함
- Evidence를 찾기 어려움
- 같은 테스트 실패가 반복됨
- CI/CD가 지나치게 복잡함
- 승인 지점이 너무 많거나 너무 적음
- Agent 권한이 과도함
- 배포 후 문제를 발견하기 어려움
- 특정 Tool에 지나치게 의존함
- 문서와 실제 코드가 자주 불일치함
- 운영 기록이 실제 사실과 섞임

### Governance 개선 흐름

AI가 Governance 개선 기회를 먼저 발견하고 제안하는 것을 기본 동작으로 한다.

```text
Continuous Observation
→ Problem / Failure / Improvement Opportunity
→ Impact Analysis
→ Governance Change Proposal
→ Review
→ Version Decision
→ Governance Update
→ Changelog
→ Apply to Projects
→ Re-evaluate
```

AI는 실제 운영에서 발견한 문제뿐 아니라 장기 유지보수성, 반복 패턴, 구조적 Drift를 근거로 Governance·Version·Branch·CI/CD 관리 개선을 먼저 제안할 수 있다.

### Governance 변경 적합성 검토

Governance는 규칙의 수가 많을수록 좋은 것이 아니다. 새로운 규칙이나 자동화 장치를 추가하기 전에 다음 네 가지를 확인한다.

1. **실제이고 일반화 가능한 문제인가?** — 실제 실패·반복·운영 관찰로 근거가 있으며 특정 Project / Tool의 일회성 문제를 넘어서는가?
2. **기존 규칙으로 막을 수 없는가?** — 기존 규칙의 명확화, 절차 개선, 기존 검증 활용만으로 해결할 수 없는가?
3. **가장 단순한 해법인가?** — 새 파일·스크립트·상태·CI gate보다 더 단순한 해결책이 없는가?
4. **효과를 확인할 수 있는가?** — 재발 방지 효과를 검증할 수 있고 추가된 유지보수 비용을 정당화할 수 있는가?

네 질문 중 하나라도 충족하지 못하면 Governance를 변경하지 않고 문제를 History / Active Issue / 개발 절차에 기록하며 관찰을 계속한다.

새로운 자동화, parser, registry, workflow 또는 상태 계층은 마지막 수단으로 취급한다. 더 단순한 절차와 기존 검증으로 같은 안전성을 얻을 수 있다면 새로운 구조를 추가하지 않는다.

새로운 버전에는 가능한 경우 **어떤 실제 경험 또는 운영 관찰이 해당 변경을 촉발했는지** 기록한다.

---



## 29. Governance 변경 관리

Governance 자체도 일반 소프트웨어와 유사한 변경 관리 원칙을 적용한다.

### Branch 관리

Branch는 변경 목적과 수명을 명확히 구분하여 관리한다.

- 일반적인 작업은 목적이 명확한 작업 Branch에서 수행한다.
- 작업 완료, Merge 또는 폐기 이후 불필요한 Branch는 정리한다.
- 오래된 Branch, 중복 Branch, 더 이상 목적이 없는 Branch는 AI가 먼저 식별하고 정리 필요성을 제안한다.
- Branch 전략을 변경할 필요가 있으면 현재 CI/CD와 Merge 흐름에 미치는 영향을 검토한 뒤 제안한다.
- Branch 보호나 Repository 정책처럼 AI가 현재 권한으로 직접 변경할 수 없는 항목은 임의 우회하지 않고 제한사항과 필요한 조치를 보고한다.

가능한 경우 다음 흐름을 사용한다.

```text
Problem
→ Proposal
→ Branch
→ Change
→ Review
→ CI / Validation
→ Human Approval
→ Merge
→ Release
```

### 변경 시 확인할 사항

- 기존 규칙과의 충돌 여부
- 기존 프로젝트에 미치는 영향
- 새 규칙의 적용 가능성
- 문서 구조와의 일관성
- 버전 변경 필요성
- Changelog 반영
- 관련 ADR 반영
- Template 반영

운영 규칙을 변경했다고 해서 모든 기존 프로젝트의 문서를 즉시 대규모로 다시 작성할 필요는 없다. Migration이 필요한 경우 영향과 우선순위를 별도로 판단한다.

---



## 30. 시작 프롬프트 최소화 원칙

새로운 AI Coding Agent를 시작할 때 Governance 전문을 매번 복사하지 않는다.

운영 규칙은 이 Repository에서 관리하고, 시작 메시지는 **Governance Repository의 위치만 알려주는 수준으로 최소화**한다.

권장 시작 메시지는 `AGENT_START.md`를 기준으로 한다.

Agent는 시작 후 해당 파일에서 안내하는 Governance와 현재 프로젝트 문서를 읽어야 한다.

---

## 31. 프로젝트별 예외

이 Governance는 공통 원칙이며 모든 프로젝트에 기계적으로 동일한 구현을 강제하지 않는다.

프로젝트 특성상 일부 규칙을 다르게 적용할 필요가 있다면 다음을 명확하게 한다.

```text
General Governance Rule
Project-specific Exception
Reason
Scope
Duration
Review Condition
```

예외가 반복적으로 여러 프로젝트에서 필요해지면 Governance 자체에 정식 규칙으로 승격할지 검토한다.

---

## 32. 최종 원칙

다음 원칙을 모든 세부 규칙의 기준으로 사용한다.

1. **현재 상태를 이해하기 전에 수정하지 않는다.**
2. **코드보다 요구사항 충족과 검증 결과를 중요하게 본다.**
3. **기존 구조가 정상적이면 최소 변경을 우선한다.**
4. **위험한 변경에는 Human Approval을 둔다.**
5. **실제 수행 결과와 추론을 구분한다.**
6. **Repository와 문서를 통해 Context를 복구할 수 있어야 한다.**
7. **중요한 결과는 재현 가능하고 추적 가능해야 한다.**
8. **실패도 지식으로 기록하고 같은 실패를 반복하지 않도록 한다.**
9. **운영 규칙 자체도 실제 경험을 바탕으로 지속적으로 개선한다.**
10. **장기적으로 더 안정적이고 확장 가능한 개발 시스템을 만든다.**
11. **자율 실행은 실행 가능성, 지침·기획과의 합치, 권한·위험 범위를 모두 충족할 때만 수행한다.**
12. **기술적으로 구현 가능하더라도 개발지침·Project Plan·Requirement·Architecture Constraint와 충돌하면 임의 실행하거나 우회하지 않는다.**
13. **AI가 자율적으로 완료할 수 없는 기술적 한계 또는 중요한 규정·기획 충돌은 숨기지 않고 근거와 영향과 함께 보고한다.**
14. **Governance, Version, Branch, CI/CD 및 프로젝트 운영 구조의 개선 필요성을 AI가 선제적으로 점검하고 먼저 제안한다.**
15. **현재 미해결 이슈는 Active Issue로 별도 관리하고, 해결 여부를 Development History 전체를 다시 읽어 판단하게 만들지 않는다.**
