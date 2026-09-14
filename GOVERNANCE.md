# AI Coding Agent 프로젝트 개발 및 운영 지침

**Version: 1.0.0**

## 1. 기본 목적

이 프로젝트는 단순히 기능을 구현하는 것을 목적으로 하지 않는다.

AI Coding Agent를 활용하여 요구사항 분석부터 개발, 검증, 배포, 유지보수까지 이어지는 지속적이고 확장 가능한 소프트웨어 개발 시스템을 구축하고 운영하는 것을 목표로 한다.

현재 요구사항을 빠르게 구현하는 것만을 최우선으로 하지 않는다. 향후 10번, 100번의 변경이 발생하더라도 구조가 유지되고, 새로운 기능·모델·검증 방식·환경을 쉽게 추가하거나 교체할 수 있는 구조를 우선한다.

또한 실제 개발 경험에서 발견된 문제와 개선점을 운영 규칙에 반영하여, **프로젝트 코드와 AI Coding Agent를 사용하는 개발 시스템을 함께 발전**시킨다.

---

## 2. 프로젝트 시작 시 수행 순서

새로운 프로젝트가 시작되면 주제와 구현에 앞서 현재 개발 및 배포 환경을 파악한다.

우선 다음을 확인한다.

- GitHub Repository와 접근 권한
- Default Branch와 Branch 구조
- 최근 Commit과 현재 코드 상태
- 파일·디렉터리 구조
- Runtime, Framework, Library, Dependency
- CI/CD 구성과 자동화 수준
- 사람이 직접 수행하는 단계
- Render 등의 배포 환경
- Workspace, Project, Environment, Service
- GitHub와 배포 환경의 연결 관계
- Auto Deploy 여부
- 환경변수 및 배포 설정
- 테스트 및 검증 구조
- 현재 존재하는 개발상의 제약사항

프로젝트가 이미 존재한다면 기존 구조를 먼저 이해한 후 변경한다. 현재 구조를 이해하지 않은 상태에서 임의로 전체 구조를 재작성하지 않는다.

---

## 3. GitHub를 공식 원본으로 사용한다

GitHub Repository를 프로젝트의 공식 Source of Truth로 사용한다.

기본 개발 흐름은 다음과 같다.

`Requirement → AI Coding Agent → Code → Verification → GitHub → CI/CD → Deployment → Post-deployment Verification`

Local Git은 기본 개발 경로로 사용하지 않는다. 필요한 경우에만 로컬 개발, 별도 테스트, 디버깅 또는 도구 사용을 위해 활용한다.

가능한 경우 코드뿐 아니라 배포·인프라 설정도 Git으로 관리하여 환경 설정의 재현성을 높인다.

---

## 4. AI Coding Agent의 역할

AI Coding Agent는 단순한 코드 생성기가 아니라 개발 사이클의 실행 주체로 활용한다.

가능한 경우 다음을 수행한다.

- 요구사항 분석
- 기존 코드 및 아키텍처 분석
- 변경 영향 범위 분석
- 구현 계획 수립
- Architecture 제안
- 코드 작성 및 수정
- 테스트 작성
- Build / Test / 실행
- 오류·로그 분석과 반복 수정
- Regression Test
- 배포 전·후 검증
- 결과 정리
- Evidence 생성

단순히 코드가 작성되었다는 것을 성공으로 간주하지 않는다. **요구사항을 충족하고 검증 가능한 상태가 되었는지**를 작업 완료 기준으로 삼는다.

---

## 5. Agent Harness를 구성한다

AI Coding Agent가 실제 개발 작업을 안정적으로 수행할 수 있도록 필요한 실행환경과 도구를 Agent Harness로 구성한다.

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
- 로그·결과 수집
- Deployment Environment
- 상태·Context 관리
- 정책·제약사항
- 권한 관리
- Evidence 관리

Agent Harness는 단순한 AI 도구 모음이 아니라 AI Agent가 작업을 수행하고 결과를 검증하며 제한된 권한 안에서 행동하도록 만드는 실행·통제 환경이다.

---

## 6. 개발의 모듈화와 유지보수성

프로젝트 초기 Architecture를 설계할 때 유지보수성과 재사용성을 중요한 목표로 둔다.

가능한 경우 다음 원칙을 적용한다.

- 기능별 모듈화
- 모델별 모듈화
- 명확한 Interface 정의
- 낮은 결합도와 높은 응집도
- 구현과 Interface 분리
- Configuration과 Implementation 분리
- Production Code와 Test Code 분리
- 환경 설정 분리
- 교체 가능한 구조
- 확장 가능한 디렉터리 구조
- 공통 기능의 재사용 가능한 구성

초기 개발 속도를 조금 희생하더라도 향후 변경 비용을 낮추는 구조를 우선한다.

---

## 7. 복잡한 모델 및 다중 모델 프로젝트

여러 모델이 존재하거나 모델의 조합·교체·추가가 예상되는 경우 이를 초기 Architecture에서 고려한다.

다음을 지원할 수 있도록 설계한다.

- 여러 모델의 독립적 개발
- 모델 추가·제거·교체
- 모델 조합
- 모델 Version 관리
- 모델 Configuration
- 검증 모델 / Reference Model / Oracle
- Dataset별 검증
- 모델별 Regression Test

필요한 경우 공통 Model Interface 또는 Adapter 구조를 사용하여 특정 모델 변경이 전체 시스템에 미치는 영향을 최소화한다. 모델 자체와 모델의 선택·조합·구성 정보를 가능한 한 분리한다.

---

## 8. 반복적인 변경을 기본 전제로 한다

프로젝트는 한 번 작성하고 끝나는 것으로 생각하지 않는다.

`Modify → Build → Test → Analyze Failure → Modify → Regression Test → Verify`

AI Agent가 반복적으로 수정하더라도 Architecture가 점점 복잡해지거나 훼손되지 않도록 한다. 수정 횟수가 증가해도 테스트와 검증 능력이 유지되도록 Regression Test를 축적한다.

---

## 9. AI 자동 수정의 제한과 Escalation

AI Agent가 테스트 실패를 스스로 분석하고 수정하는 자동 반복 루프를 사용할 수 있다.

단, 무한 반복을 방지하기 위해 프로젝트에 적절한 조건을 둔다.

- 최대 재시도 횟수
- 실행 시간 제한
- 비용 제한
- 동일 오류 반복 감지
- 구조적 변경이 필요한 경우 Human Review 전환

자동 수정으로 해결되지 않는 경우 사용자에게 상황과 원인을 명확하게 전달하고 판단을 요청한다.

---

## 10. CI/CD를 프로젝트 특성에 맞게 구성한다

모든 프로젝트에 동일한 수준의 CI/CD를 적용하지 않는다.

위험도, 복잡도, 사용자 영향, 안전 요구사항, 데이터 중요도, 배포 빈도, 비용, 검증 가능성을 고려하여 수준을 결정한다.

일반적인 IT 서비스에서는 `Commit → Basic Checks → Test → Deploy → Smoke Test` 정도로 구성할 수 있다.

높은 신뢰성이 요구되는 시스템에서는 `Requirement → Static Analysis → Unit Test → Integration Test → Simulation → HIL → Release Verification` 등 더 엄격한 검증 구조를 사용할 수 있다.

CI는 단순한 자동 테스트가 아니라 **Agent와 개발자의 변경을 통제하는 Quality Gate**로 활용한다.

---

## 11. 검증과 Evidence

검증 결과는 재현 가능하고 추적 가능하도록 기록한다.

가능한 경우 다음 정보를 연결한다.

- Requirement
- Code Change
- Commit
- Build
- Test
- Test Result
- Dataset
- Model Version
- Configuration
- Deployment
- Post-deployment Verification

단순히 PASS라고 기록하지 말고 무엇을 어떤 조건에서 검증하여 PASS가 되었는지 남긴다.

가능하면 Evidence를 사람이 읽을 수 있는 형태뿐 아니라 Agent가 다시 사용할 수 있는 구조화된 형태로도 저장한다.

---

## 12. 재현성

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

특히 모델 기반 시스템에서는 어떤 모델 + 어떤 데이터 + 어떤 Configuration + 어떤 Code에서 나온 결과인지 추적할 수 있도록 설계한다.

---

## 13. 변경 범위를 최소화한다

기존 코드가 정상적으로 동작하고 있다면 가능한 한 유지한다. 요구사항 충족에 필요한 최소 범위만 수정한다.

특별한 이유가 없는 한 다음을 피한다.

- 전체 파일의 불필요한 재작성
- 무관한 리팩터링
- 요구사항과 관계없는 구조 변경
- 단순 기능 추가를 위한 전체 Architecture 재구성

Architecture를 변경해야 하는 경우 변경 이유와 영향 범위를 먼저 설명한다.

---

## 14. Git 변경 및 사용자 승인

AI가 실제 GitHub Repository를 변경할 수 있는 환경에서는 위험도가 높은 단계를 Human Approval 대상으로 둔다.

일반적으로 자동 수행 가능한 작업:

- Repository 읽기
- 코드 분석
- 변경안 작성
- 테스트 계획 작성
- 테스트 수행
- Branch에서 작업
- CI 실행
- PR 생성

사용자 승인 후 수행하는 작업:

- 공식 Branch에 Commit / Push
- 파일 삭제
- Branch 삭제
- Merge
- Production에 영향을 주는 변경
- 대규모 Architecture 변경
- 신규 외부 Dependency 도입
- 라이선스에 영향을 줄 수 있는 변경

목표는 AI의 모든 동작을 수동 승인하는 것이 아니라 **위험한 단계에만 Human Approval을 배치하는 것**이다.

---

## 15. Version 관리

사용자에게 표시되는 Project Version은 임의로 증가시키지 않는다.

Version 변경이 필요하다고 판단하면 `현재 Version 확인 → 변경 필요성 설명 → 변경 Version 협의 → 합의 후 변경` 순서로 진행한다.

---

## 16. Open Source 및 외부 Dependency

새로운 Library, Framework, Model, Tool 또는 외부 코드를 사용할 경우 도입 전에 가능한 범위에서 다음을 확인한다.

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

조건이 불명확하거나 중요한 영향을 줄 수 있는 경우 사용자에게 알리고 승인을 받은 후 도입한다.

---

## 17. 보안 및 권한

AI Agent에게 필요한 최소한의 권한만 제공하는 것을 원칙으로 한다.

가능한 경우 권한을 `Read / Modify / Test / Deploy / Production Change / Destructive Action`으로 분리한다.

특히 Production Database 삭제, Production Service 삭제, 중요 데이터 삭제, Secret 변경, Production 배포, 복구 불가능한 변경은 자동 수행을 제한한다.

가능한 한 AI가 실수하더라도 시스템적으로 치명적인 작업을 실행하지 못하도록 설계한다.

---

## 18. Deployment와 Post-deployment Verification

배포 성공과 서비스 정상 동작을 동일하게 취급하지 않는다.

기본적으로 `GitHub → CI → Deploy → Health Check → Smoke Test → Result` 흐름을 고려한다.

서비스 특성에 따라 HTTP 응답, API 정상 여부, 주요 기능, 브라우저 로딩, 핵심 데이터, Error Rate, Latency 등을 자동으로 확인할 수 있다.

---

## 19. Observability

프로젝트가 운영 단계로 발전할 가능성이 있다면 개발과 배포 이후의 상태를 관찰할 수 있는 구조를 고려한다.

가능한 경우 Log, Error, Health, Performance, API Failure, Resource Usage, Deployment State를 수집한다.

운영 중 문제가 발생할 경우 원인 파악과 Rollback 또는 Repair가 가능하도록 한다.

---

## 20. 변경 이력과 Traceability

프로젝트가 커질수록 다음 관계를 추적할 수 있도록 한다.

`Requirement → Change → Commit → Build → Test → Deploy → Evidence`

모델 기반 또는 검증이 중요한 프로젝트에서는 변경의 근거와 검증 결과를 함께 보존한다.

---

## 21. 개발 과정에서의 지속적인 개선 제안

AI Coding Agent는 사용자 요청 작업만 수행하는 것에 그치지 않는다.

개발 과정에서 현재 방식보다 더 나은 Architecture, 테스트, Tool, CI/CD, 유지보수 방식 또는 보안·라이선스 대안을 발견하면 적절한 시점에 사용자에게 피드백한다.

피드백은 다음 경우를 우선한다.

- 현재 구조가 향후 확장에 문제가 될 가능성이 발견된 경우
- 반복되는 수정이 구조적 문제에서 발생하는 경우
- 새로운 Tool이나 Framework가 명확히 유리한 경우
- 테스트 또는 검증 체계를 개선할 수 있는 경우
- 유지보수 비용을 크게 줄일 수 있는 경우
- 보안 또는 라이선스 위험이 발견된 경우
- 더 적합한 Architecture로 발전할 수 있는 경우

이러한 피드백은 현재 요구사항에 대한 작업과 별도로 명확하게 구분한다.

---

## 22. 최종 개발 방향

최종적으로 다음 구조를 지향한다.

`User Requirement → AI Coding Agent → Agent Harness → Architecture / Code / Model Development → Automated Verification → Evidence → Human Approval → GitHub → CI/CD → Deployment → Post-deployment Verification → Observability → Feedback / Improvement`

프로젝트 규모가 커지더라도 동일한 원칙을 확장할 수 있도록 설계한다. 현재의 빠른 구현보다 장기적인 유지보수성, 재사용성, 확장성, 검증 가능성, 재현성 및 안정성을 우선한다.

---

## 23. 프로젝트 지식 및 개발 이력 관리

GitHub Repository는 Source Code 저장소일 뿐 아니라 프로젝트의 개발 지식과 의사결정의 공식 기록 저장소로 사용한다.

새로운 참여자 또는 새로운 AI Coding Agent가 Repository를 확인하면 가능한 범위에서 다음을 이해할 수 있어야 한다.

- 프로젝트가 왜 시작되었는가
- 초기 요구사항은 무엇이었는가
- 어떤 Architecture를 선택했는가
- 어떤 설계 대안을 검토했는가
- 왜 현재 구조를 선택했는가
- 어떤 기능이 언제 추가되었는가
- 어떤 문제가 발생했는가
- 어떻게 해결했는가
- 어떤 결정이 보류되었는가
- 현재 시스템의 한계는 무엇인가
- 앞으로 어떤 방향으로 발전할 예정인가

README는 현재 상태와 사용 안내를 위한 문서로 유지하고, 전체 개발 과정은 별도의 개발 기록 문서에 누적한다.

권장 구조:

```text
README.md
GOVERNANCE.md
VERSION
CHANGELOG.md

docs/
├── CURRENT_STATUS.md
├── DEVELOPMENT_HISTORY.md
├── ARCHITECTURE.md
├── ADR/
└── evidence/
```

### DEVELOPMENT_HISTORY.md

프로젝트 시작부터 중요한 개발 과정을 시간순으로 기록한다. 가능한 경우 다음을 포함한다.

`Date / Requirement / Problem / Context / Options Considered / Decision / Reason / Implementation / Changed Files / Verification / Deployment / Result / Known Issues / Next Step`

단순히 무엇을 수정했는지만 기록하지 말고 왜 수정했는지를 기록한다.

### CURRENT_STATUS.md

현재 프로젝트의 상태를 빠르게 복구할 수 있도록 유지한다.

가능한 경우 다음을 포함한다.

`Current Version / Current Commit / Current Branch / Deployment Status / Runtime / Architecture State / Implemented Features / Known Issues / Current Limitations / Pending Decisions / Next Development Target`

### Decision 기록

중요한 설계 결정은 가능한 경우 다음 형식으로 기록한다.

`Decision / Context / Options / Selected Option / Reason / Consequences / Revisit Condition`

### AI 제안과 사용자 결정의 구분

중요한 Architecture 및 Product 결정에서는 가능한 경우 다음을 구분한다.

`AI Proposal / User Decision / Implementation / Result`

AI가 제안한 방법과 사용자가 최종적으로 선택한 방법을 동일한 것으로 기록하지 않는다.

### 실패 및 복구 기록

중요한 실패도 기록한다. 가능한 경우 `Symptom / Root Cause / Impact / Resolution / Verification / Prevention`을 남긴다.

### Evidence와 Traceability

가능한 경우 다음 흐름을 추적한다.

`Requirement → Decision → Code Change → Commit → Build → Test → Deployment → Post-deployment Verification → Evidence`

필요하면 `REQ-001`, `CHANGE-014`, `TEST-042`, `DEPLOY-019`, `EVIDENCE-031`과 같은 식별자를 단계적으로 도입할 수 있다.

### Agent Context 관리

새로운 AI Coding Agent 또는 새로운 ChatGPT 대화에서 기존 개발 상태를 빠르게 복구할 수 있도록 프로젝트 핵심 Context를 GitHub에 저장한다. 채팅 내용 자체를 유일한 지식 저장소로 사용하지 않는다.

우선적으로 다음 문서를 Context 복구에 활용한다.

`CURRENT_STATUS.md / DEVELOPMENT_HISTORY.md / ARCHITECTURE.md / PRODUCT_BRIEF.md / ADR/`

### 기록의 정확성

개발 기록은 실제 발생한 사실과 당시의 의사결정을 기준으로 작성한다.

추후 결과를 알고 있는 상태에서 과거 결정이 마치 처음부터 의도된 것처럼 기록하지 않는다.

- 실제 수행하지 않은 테스트를 수행했다고 기록하지 않는다.
- 확인하지 않은 배포 결과를 성공했다고 기록하지 않는다.
- AI의 추론과 실제 검증 결과를 구분한다.
- 계획과 실제 구현 결과를 구분한다.

개발 기록은 유지보수와 장애 분석에 사용할 수 있으므로 재현 가능하고 사실 기반으로 유지한다.

---

## 24. 운영 규칙 자체의 지속적 개선

이 운영 지침은 완성된 규칙으로 취급하지 않는다.

실제 프로젝트 개발에서 발견되는 문제를 관찰하고, 반복적으로 발생하는 실패·비효율·누락을 이 저장소의 변경 근거로 삼아 지침을 개선한다.

예:

```text
실제 프로젝트 경험
      ↓
문제 / 실패 / 불편
      ↓
원인 분석
      ↓
Governance 개선안
      ↓
Version 증가
      ↓
실제 프로젝트에 적용
      ↓
결과 검증
      ↓
다음 개선
```

운영 규칙 변경 시 가능한 경우 다음을 함께 기록한다.

- 어떤 프로젝트 경험이 변경을 촉발했는가
- 기존 규칙의 어떤 한계가 있었는가
- 무엇을 변경했는가
- 변경이 어떤 문제를 예방 또는 개선하는가
- 실제 프로젝트에 적용했을 때 결과가 어땠는가

운영 규칙의 진화 자체도 프로젝트의 공식 개발 이력으로 관리한다.
