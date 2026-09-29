## 41. 2026-09-29 — Requirement Contract protection and change-control guard

### Requirement

사용자가 한 번 요청하고 구현·검증한 동작이 후속 개발 과정에서 새로운 작업의 부작용으로 원복되는 문제를 구조적으로 방지해야 합니다. 특히 최근 사람 수 즉시 표시 요구사항이 반복적으로 회귀했기 때문에, 채팅 Context가 아니라 Repository와 CI가 해당 결정을 기억해야 합니다.

### Decision

사용자 요청으로 확정된 유지 필요 동작을 project-level **Requirement Contract**로 등록하고 다음 규칙을 적용합니다.

- `ACTIVE` Contract는 후속 작업에서 유지해야 하는 제품 계약입니다.
- 내부 구현 리팩터링은 허용하되 사용자 관찰 가능 동작과 회귀 테스트는 유지합니다.
- 기존 Contract와 새 요구사항이 충돌하면 조용히 원복하지 않고 충돌/영향/대안을 사용자에게 보고합니다.
- Contract 정의나 회귀 테스트를 의도적으로 변경할 경우 `CONTRACT-CHANGE: <ID>` 선언을 요구합니다.
- CI는 Contract Registry의 구조와 회귀 테스트 존재 여부를 자동 검사하고, 보호된 구현 경로가 변경되었음을 경고합니다.

### Implementation

- `docs/requirement_contracts.json` 추가
- `docs/REQUIREMENT_CONTRACTS.md` 추가
- `tools/validate_requirement_contracts.py` 추가
- `tests/test_requirement_contracts.py` 추가
- 필수 `janggi-validation.yml`에 Contract validation 추가
- `AGENTS.md`, `AGENT_START.md`, `CURRENT_STATUS.md`에 Contract 확인 절차 추가
- 공통 Governance를 `1.1.0`으로 올리고 Requirement Contract 보호 규칙 추가

### Current protected contract

`UX-001`: 사용자가 합법적인 수를 선택하면 AI 계산이 시작되기 전에 사용자 수가 장기판에 먼저 보입니다.

### Verification

- Contract Registry 자체 검증
- 참조 회귀 테스트 존재 여부 AST 검증
- Pull Request / direct push에서 Contract 변경 선언을 검사하도록 CI 경계 구성

### Boundary

모든 구현 파일 수정을 막는 것은 아닙니다. 보호 경로 내부의 리팩터링은 회귀 테스트가 Contract를 계속 증명하는 한 허용합니다. 실제 제품 동작을 변경해야 하는 경우에만 Contract change로 승격합니다.

### Next Step

향후 사용자가 새로운 핵심 요구사항을 확정할 때 동일한 Contract ID를 발급하고 회귀 테스트를 연결합니다.

---

## 31. 2026-09-21 — Adaptive selection diversity bound

### Requirement

반복 오답 문제를 우선하는 정책은 유용하지만, bounded 후보 집합에서 반복 오답 후보가 많을 경우 다른 실수 유형을 거의 보여주지 못하는 고착 문제가 생길 수 있습니다.

### Decision

반복 오답 후보의 우선순위는 유지하되, 요청된 문제 수가 2개 이상이고 다른 후보가 존재하는 경우 반복 오답 후보를 대략 절반까지로 제한합니다. 남은 슬롯은 아직 선택되지 않은 reason을 우선하는 후보를 채운 뒤 기존 순서를 사용합니다.

- `max_problems=5`이면 반복 오답 후보는 최대 3개
- 다른 후보가 없으면 반복 오답 후보를 제한하지 않음
- 반복 오답 우선 자체는 유지
- 선택은 여전히 현재 세션의 ephemeral metrics만 사용
- persistence/mastery/difficulty model 미도입

### Implementation

- adaptive selector에 repeated-mistake quota 추가
- 남은 슬롯에서 선택되지 않은 reason을 우선하는 diversity 정렬 추가
- 반복 오답 고착 및 reason 다양성 회귀 테스트 추가
- 브라우저에 문제 다양성 정책이 적용되었음을 표시
- `TRAINING_PROBLEMS.md`, `CURRENT_STATUS.md` 동기화

### Boundary

이 정책은 문제 목록의 노출 순서와 구성만 조정합니다. 반복 오답을 해결했다고 판단하거나 사용자의 장기 숙련도를 추정하지 않습니다.

### Next Step

실제 사용에서 이 bounded diversity가 반복 실수 재학습과 문제 유형 폭 사이의 균형을 유지하는지 확인하고, 필요성이 있을 때만 더 정교한 spacing policy를 검토합니다.

---
## 30. 2026-09-21 — Repeated training-mistake prioritization

### Requirement

reason별 정확도만으로는 같은 포지션을 계속 틀리는 상황을 직접 표현하지 못합니다. 이미 legal training answer 결과가 세션에 존재하므로, 반복 오답 문제를 별도 영속 데이터 없이 바로 다음 문제 선택에 활용할 수 있습니다.

### Decision

세션 지표에 problem id별 시도 횟수와 오답 횟수를 추가하고, adaptive selector가 **반복 오답이 확인된 문제 → 오답이 있는 낮은 reason별 정확도** 순으로 기존 문제를 재정렬하도록 확장했습니다.

- `problem_attempts` / `problem_incorrect`는 현재 세션에만 존재
- 같은 문제를 여러 번 틀릴수록 해당 문제를 다음 문제 목록 앞쪽으로 이동
- 반복 오답 문제가 없으면 기존 reason 기반 우선순위 사용
- adaptive selection은 여전히 최대 20개 후보/기본 5개 문제 범위 내에서만 동작
- persistence/mastery/학습 난이도 모델은 추가하지 않음

### Implementation

- `TrainingMetricsSnapshot`에 problem-level counts 추가
- `adaptive_problem_priority()` 추가
- `select_adaptive_training_problems()`에서 repeated mistake 우선 처리
- `/api/training/problems`에 `priority_problem_ids` 추가
- metrics 응답에 problem-level counts 노출
- 브라우저 훈련 패널에 반복 오답 우선 메시지 표시
- unit/API/browser contract 테스트 추가
- `TRAINING_METRICS.md`, `TRAINING_PROBLEMS.md`, `API.md`, `CURRENT_STATUS.md` 동기화

### Boundary

반복 오답은 동일한 세션 내 legal answer 결과만으로 판정합니다. 이것을 장기적인 사용자 능력, 문제의 절대 난이도, 또는 model-training label로 해석하지 않습니다.

### Next Step

반복 오답 재출제 흐름이 실제 사용에서 지나치게 같은 문제에 고착되는지 확인하고, 필요할 때만 재노출 상한이나 다양성 정책을 설계합니다.

---
## 29. 2026-09-21 — Session-local adaptive training problem selection

### Requirement

단순히 최근 복기 문제를 다시 보여주는 것보다, 현재 세션에서 실제로 틀린 실수 유형을 다음 훈련 문제에서 먼저 다루는 것이 자연스러운 다음 단계였습니다. 다만 현재 지표는 샘플이 작고 ephemeral이므로 장기 숙련도나 난이도 모델로 확대하면 안 됩니다.

### Decision

기존 review-derived training problems를 최대 20개까지 후보로 만든 뒤, 현재 `TrainingMetricsSnapshot`의 reason별 시도/정답 수를 사용해 **관찰된 오답이 있고 정확도가 낮은 reason**을 우선하는 session-local selection policy를 추가했습니다.

- 문제 자체의 생성 규칙은 변경하지 않음
- 기존 문제를 재정렬할 뿐 새로운 증거나 label을 생성하지 않음
- 관찰된 reason-specific mistake가 없으면 기존 recent-first 순서 유지
- 기본 최대 5개, 전체 후보 최대 20개
- persistence/mastery/difficulty model 미도입

### Implementation

- `adaptive_reason_priority()` 추가
- `select_adaptive_training_problems()` 추가
- `/api/training/problems`가 최대 20개 후보를 만든 뒤 현재 session metrics로 재선택하도록 변경
- 응답에 `priority_reason_codes` 추가
- 브라우저에서 적응형 선택 여부와 전체/이유별 정답률을 함께 표시
- selector unit/API/browser contract 테스트 추가
- `TRAINING_PROBLEMS.md`, `TRAINING_METRICS.md`, `API.md`, `CURRENT_STATUS.md` 동기화

### Boundary

reason-specific 정확도는 현재 세션의 관찰치일 뿐 mastery estimate가 아닙니다. 작은 표본의 일시적인 0%/100%도 장기적인 난이도나 사용자 능력으로 해석하지 않습니다.

### Next Step

실제 사용 흐름에서 adaptive selection이 원하는 문제를 반복적으로 앞으로 가져오는지 확인하고, 필요성이 입증될 때만 별도 persistence 요구사항을 검토합니다.

---

## 28. 2026-09-21 — Reason-specific training accuracy

### Requirement

전체 훈련 정답률만으로는 어떤 실수 유형이 여전히 어려운지 확인하기 어렵기 때문에, 기존 `reason_codes`를 세션 지표와 직접 연결했습니다.

### Decision

각 legal training attempt에서 문제에 포함된 reason code별 시도 수와 정답 수를 함께 집계합니다. 하나의 문제가 여러 reason code를 가지면 동일한 정답 결과가 각 해당 signal에 기록됩니다.

### Implementation

- `TrainingSessionMetrics.reason_correct` 추가
- `/api/training/metrics` 및 훈련 응답에 `reason_correct` 노출
- 브라우저 훈련 패널에서 reason별 정확도 표시
- focused unit/API/browser contract 테스트 추가
- `docs/TRAINING_METRICS.md`, `docs/API.md`, `docs/CURRENT_STATUS.md` 동기화

### Boundary

reason-specific accuracy는 현재 세션의 interaction 분석용 지표일 뿐, 장기적인 사용자 능력 추정이나 training label이 아닙니다.

### Next Step

실제 사용자 세션에서 이 지표가 반복적으로 유용한지 확인한 뒤 persistence 또는 문제 난이도 조정 정책을 별도 설계합니다.

---

## 27. 2026-09-21 — Ephemeral training session metrics

### Requirement

포지션 훈련 기능이 실제 학습 interaction으로 이어지는지 최소한 측정할 수 있는 지표가 필요했습니다. 다만 persistence 요구사항이 아직 확정되지 않았기 때문에 현재 프로세스와 match 세션에만 한정했습니다.

### Decision

`janggi.training_metrics`를 별도 계층으로 두고 legal training answer 제출만 집계합니다.

- attempts / correct / incorrect
- unique problem count
- accuracy
- problem reason-code별 시도 수
- `POST /api/reset`에서 metrics 초기화
- filesystem/database/user profile에는 저장하지 않음

### Implementation

- `TrainingSessionMetrics`와 immutable `TrainingMetricsSnapshot` 추가
- `/api/training/problems` 응답에 현재 metrics 포함
- `/api/training/answer` 성공적인 legal attempt 후 metrics 갱신
- `GET /api/training/metrics` 추가
- 브라우저 훈련 패널에 현재 세션 정답률 표시
- unit/API/browser contract 테스트 추가
- `docs/TRAINING_METRICS.md` 추가

### Boundary

이 지표는 mastery나 learning gain을 의미하지 않으며, 모델 학습용 데이터나 사용자 프로필로 자동 승격되지 않습니다.

### Next Step

반복 문제를 여러 세션에서 비교할 필요가 실제로 확인될 때 persistence/계정 모델을 별도 요구사항으로 설계합니다.

---

## 26. 2026-09-21 — Position-based training problem generation

### Requirement

세션 복기에서 반복 실수 신호를 찾은 뒤, 이를 실제로 다시 풀 수 있는 학습 문제로 연결할 필요가 있었습니다. 다만 아직 persistence와 계정 모델이 없으므로 현재 세션에서만 재생 가능한 bounded interaction으로 제한했습니다.

### Decision

`ReviewEntry`가 각 착수의 pre-move `GameState`를 직접 보존하도록 확장하고, 별도 `janggi.training_problems` 계층이 비추천 착수를 포지션 문제로 변환하도록 했습니다.

- `acceptable`, `inaccuracy`, `major_mistake`만 후보
- 유효한 normalized engine recommendation이 있어야 함
- 기본 5개, 최대 20개
- 문제 생성은 Match 상태를 변경하지 않음
- 정답은 기본 API 응답에서 숨김
- 브라우저 제출은 `/api/training/answer`에서 다시 검증
- persistence, mastery, streak, user profile은 도입하지 않음

### Implementation

- `ReviewEntry.state` 추가
- `PositionTrainingProblem` 및 `generate_training_problems()` 추가
- `POST /api/training/problems` 추가
- `POST /api/training/answer` 추가
- 브라우저에 `훈련 문제 만들기`와 실제 포지션 답안 입력 흐름 추가
- 문제 생성 및 API/browser boundary 테스트 추가
- `docs/TRAINING_PROBLEMS.md` 추가
- Architecture, API, README, Current Status 동기화

### Boundary

훈련 문제는 개인 학습 interaction이지 모델 ground-truth dataset이 아닙니다. 사용자가 둔 수가 문제로 재사용되더라도 해당 수나 추천수가 persistence되거나 자동으로 training label로 승격되지는 않습니다.

### Next Step

실제 반복 문제를 여러 번 풀었을 때 학습 효과를 측정할 수 있는 최소한의 non-persistent session metric과, 그 결과를 저장할지 여부를 별도 요구사항으로 검토합니다.

---

## 25. 2026-09-21 — Bounded session review and coaching aggregation

### Requirement

`reason_codes`를 만든 다음 실제 대국에서 반복되는 실수 유형을 확인할 수 있는 최소한의 복기 경로가 필요했습니다. 아직 persistence를 도입하지 않은 MVP 단계이므로 세션 종료 후 현재 기록을 다시 분석하는 on-demand 방식으로 한정했습니다.

### Decision

새 `janggi.review` 계층을 추가해 `GameRecord → Analyzer → Coaching → aggregation` 흐름을 분리했습니다.

- 기본적으로 현재 웹 훈련기의 학습자 측인 Cho 수만 리뷰
- 최근 최대 20수, 설정상 최대 60수까지만 분석
- 원본 기록을 setup부터 replay하여 각 수의 실제 pre-move state를 복원
- `reason_codes`와 coaching severity를 집계
- 현재 `Match`와 review 상태를 변경하지 않음
- 결과를 영구 저장하지 않음

### Implementation

- `janggi.review.CoachingReview` 및 `ReviewEntry` 추가
- `review_record()`로 bounded recent-move review 구현
- `POST /api/review` 추가
- 리뷰 응답에 move, recommendation, score delta, message, next_action, reason_codes 제공
- review 단위 테스트 및 API boundary 테스트 추가
- `README.md`, `docs/API.md`, `docs/COACHING.md`, `docs/CURRENT_STATUS.md` 동기화

### Boundary

리뷰 결과는 반복 실수 집계를 위한 현재 증거이지, 자동으로 사용자 프로필이나 학습 정답을 저장하는 persistence 정책이 아닙니다. 향후 position-based training으로 연결할 때도 현재 reason/severity 신호와 실제 포지션을 함께 검토해야 합니다.

### Next Step

리뷰에서 식별된 반복 문제를 실제 훈련 문제로 변환하는 position-based training 문제 생성 계층을 검토합니다. persistence 도입은 별도 요구사항으로 유지합니다.

---

## 24. 2026-09-21 — Structured coaching reason codes

### Requirement

현재 코칭 메시지는 학습자에게는 유용하지만, 향후 반복 실수 추적이나 포지션 기반 훈련을 위해서는 한글 설명 문장을 다시 파싱하지 않고도 안정적으로 집계할 수 있는 구조화된 신호가 필요했습니다.

### Decision

기존 `CoachingInsight`에 `reason_codes`를 추가하고, 코칭 계층이 `MoveAnalysis`에서 직접 안정적인 machine-readable 신호를 생성하도록 했습니다.

현재 코드:

- `hanging_piece`
- `immediate_capture`
- `double_attack`
- `score_deviation`
- `capture`
- `check`

여러 신호를 동시에 유지할 수 있도록 설계했으며, 기존 severity/message/next_action의 의미와 점수 기반 분류 규칙은 변경하지 않았습니다.

### Implementation

- `janggi.coaching.CoachingReason` 추가
- `CoachingInsight.reason_codes` 추가
- `/api/analyze/move` coaching 응답에 `reason_codes` 노출
- 코칭 단위 테스트에 신호 조합 및 unavailable 경로 검증 추가
- API boundary 테스트에서 machine-readable 리스트 계약 검증 추가
- `docs/COACHING.md`, `docs/API.md`, `docs/CURRENT_STATUS.md` 동기화

### Purpose

이 신호는 즉시 persistence를 추가하지 않고도 향후 다음 단계에서 반복되는 실수 유형 집계, 약점 추적, 포지션 기반 훈련 문제 생성의 안정적인 입력 경계를 제공합니다.

### Boundary

`reason_codes`는 분석 신호이지 새로운 전술적 truth claim이 아닙니다. 기존의 conservative severity와 bounded tactical motif 정책을 그대로 유지합니다.

### Verification

현재 branch에서 전체 compile/test CI와 API/검색 benchmark 결과를 확인한 뒤 main 반영 여부를 결정합니다.

### Next Step

reason code를 실제 사용자 세션/복기 데이터에 누적하는 persistence 단계는 별도 요구사항과 저장 구조를 검토한 뒤 진행합니다.

---

# Personal AI Janggi Trainer — 개발 이력

이 문서는 README와 역할을 분리해, 프로젝트의 **초기 기획부터 현재 구현까지의 개발 과정과 주요 의사결정, 시행착오, 문제 해결 과정**을 시간순으로 기록합니다.

README는 현재 프로젝트를 빠르게 이해하기 위한 문서이고, 이 문서는 프로젝트가 **왜 지금의 형태가 되었는지**를 추적하기 위한 기록입니다.

---

## 23. 2026-09-15 — Tactical risk detection and coaching explanation v1

### Requirement

현재 착수 분석은 엔진 점수와 단순 품질 분류를 제공하지만, 학습자가 실제로 주의해야 할 전술적 위험을 독립적으로 이해하기에는 설명력이 부족했습니다.

### Decision

엔진의 강도나 특정 Vendor 구현에 의존하지 않는 얕은 전술 위험 신호를 `Analyzer` 계층에 추가했습니다.

현재 신호는 다음 두 단계로 제한합니다.

- `immediate_capture`: 착수한 기물을 상대가 바로 잡을 수 있으나 즉시 합법적인 되잡기가 존재함
- `hanging_piece`: 착수한 기물을 상대가 바로 잡을 수 있고, 그 직후 착수자에게 합법적인 되잡기가 없음

이 신호는 전역적으로 불리한 수임을 증명하는 강한 엔진 판정이 아니라, 학습자에게 제공할 보조 전술 신호로 정의했습니다.

### Implementation

- `janggi.analysis.TacticalRisk` 추가
- `MoveAnalysis.tactical_risk` 추가
- 이동 후 상대의 즉시 잡기와 그에 대한 즉시 되잡기 가능성을 도메인 규칙으로 검사
- `coaching.py`에서 `hanging_piece`를 명시적인 위험 설명으로 연결
- `/api/analyze/move` 응답에 `tactical_risk` 노출
- 브라우저 훈련 화면에 전술 위험 상태 표시
- protected exchange와 hanging piece를 구분하는 회귀 테스트 추가

### Verification

GitHub Actions Python validation에서 compile 및 전체 unit test가 통과했습니다.

### Scope Boundary

현재 구현은 1수 깊이의 즉시 잡기/되잡기 신호만 다룹니다. 체크 이후의 복합 전술, 2수 이상 이어지는 포크/유인/핀 등의 motif 판단은 향후 stronger analysis 계층에서 다룹니다.

### Next Step

대표적인 전술 fixture를 더 추가하여 체크·잡기·교환·희생·다음 수 전술에 대한 코칭 품질을 검증하고, 이후 필요성이 확인되면 multi-ply tactical analysis를 설계합니다.

---

## 1. 프로젝트 출발점

### 목표

개인 장기 학습자가 단순히 대국만 하는 것이 아니라, 자신의 착수를 반복적으로 복기하고 다음 수를 개선할 수 있도록 돕는 **개인용 AI 장기 코치**를 만드는 것을 목표로 시작했습니다.

핵심 방향은 단순한 장기 AI가 아니라 다음 학습 루프입니다.

```text
사용자 착수
  ↓
AI 분석
  ↓
왜 좋은지 / 왜 나쁜지 설명
  ↓
다음에 무엇을 봐야 하는지 제시
  ↓
반복 학습
  ↓
사용자의 반복 실수 축적
  ↓
개인 맞춤형 훈련
```

초기 MVP에서는 한 번에 모든 기능을 구현하지 않고, 장기 규칙과 대국 상태를 신뢰할 수 있는 기반으로 먼저 만들고 그 위에 분석·검색·학습 기능을 단계적으로 추가하는 방향으로 결정했습니다.

---

## 2. 개발·배포 운영 원칙 수립

프로젝트의 Source of Truth는 GitHub로 정했습니다.

```text
사용자
  ↓
ChatGPT
  ↓
GitHub 저장소 직접 접근
  ↓
코드 확인/수정
  ↓
변경 내용과 영향 확인
  ↓
GitHub commit
  ↓
Render 자동 배포
  ↓
웹 서비스 확인
```

주요 원칙:

- GitHub commit 이력을 변경 이력으로 사용
- 로컬 Git/로컬 실행을 기본 개발 파이프라인에서 제외
- 기존 기능을 유지하면서 최소 변경
- 버전 번호는 임의로 변경하지 않음
- 외부 의존성은 필요성을 검토하고 라이선스를 확인한 후 추가
- 도메인 규칙은 웹 UI가 아니라 Python 도메인 모델이 최종 권한을 가짐

---

## 3. 장기 도메인 모델 구축

가장 먼저 9×10 장기판을 표현하는 독립적인 도메인 모델을 구축했습니다.

주요 범위:

- 초/한 진영
- 장군, 사, 상, 마, 차, 포, 졸/병
- 기본 초기 배치 및 장기 특유의 마/상 배치 교환 형태
- 기물별 이동 규칙
- 마/상의 길막 규칙
- 포의 장애물/포획 규칙
- 궁성 내부 이동 및 대각선 이동
- 장군 판정
- 자충수 방지
- 빅장 판정
- 패스
- 합법 수 생성
- 수 적용 및 수 이력
- 현재 차례를 포함한 position key

웹이나 엔진에서 규칙을 중복 구현하지 않고 `GameState`가 합법성의 최종 기준이 되도록 구조를 잡았습니다.

---

## 4. 대국 상태 및 기록 계층 추가

도메인 모델만으로 끝내지 않고 실제 학습/복기 시스템으로 확장할 수 있도록 대국 계층을 분리했습니다.

### Match

대국의 진행 상태와 종료 조건을 담당합니다.

- 진행 중 / 종료 상태
- 반복 관련 처리
- 연속 패스 무승부 정책
- 게임 종료 판단

### Game Record

대국을 구조화된 형태로 저장·복원할 수 있도록 기록 형식을 정의했습니다.

- `janggi-record-v1`
- `janggi-state-v1`
- 수순 replay
- JSON serialization
- setup 정보 복원
- 저장된 상태와 replay 결과 일치 여부 검증

이 계층을 통해 향후 사용자 대국을 단순 화면 상태가 아니라 **재생 가능한 학습 데이터**로 취급할 수 있게 했습니다.

---

## 5. 엔진 인터페이스 분리

특정 AI 구현에 웹 애플리케이션이 종속되지 않도록 엔진 경계를 별도 정의했습니다.

```text
GameState
   ↓
Engine
   ↓
EngineAnalysis
```

엔진 인터페이스와 수 검증 함수를 분리해, 현재의 단순 검색 엔진을 나중에 더 강한 검색 엔진이나 학습 모델로 교체할 수 있도록 했습니다.

핵심 원칙은 **엔진이 아무리 강력해도 실제 수 적용 전에는 장기 도메인 모델을 통과해야 한다**는 것입니다.

---

## 6. 착수 분석 계층 추가

엔진의 단순 `best_move`만 노출하지 않고, 사람이 실제로 둔 수를 분석하는 별도 계층을 추가했습니다.

한 수 분석 결과에는 다음 정보가 포함됩니다.

- 실제 착수
- 추천 수
- 착수 전 평가
- 착수 후 평가
- 평가 변화량
- 검색 깊이
- 탐색 노드 수
- principal variation
- 평가 관점

특히 초/한에 따라 엔진 점수 방향이 달라지는 문제를 해결하기 위해, 사용자에게 보여주는 점수를 **착수한 진영의 관점으로 정규화**했습니다.

---

## 7. 첫 검색 엔진 구축

외부 라이브러리에 의존하지 않는 `NegamaxEngine`을 구현했습니다.

현재 baseline은 다음 구조입니다.

```text
후보 수 생성
  ↓
각 수 적용
  ↓
Negamax
  ↓
Alpha-Beta pruning
  ↓
Material + Mobility 평가
```

현재 평가 함수는 기물 가치와 기동성을 중심으로 한 단순한 평가 함수입니다.

이 단계의 목표는 최강 장기 AI가 아니라,

1. 실제 수를 선택할 수 있고
2. 웹/API에서 호출할 수 있으며
3. 자기 대국과 코칭에 사용할 수 있는

**검증 가능한 baseline**을 만드는 것이었습니다.

---

## 8. Self-play / Training / Evaluation 기반 추가

향후 학습 모델로 확장할 수 있도록 다음 기반을 미리 구축했습니다.

- self-play 대국 생성
- completed record 검증
- position/action/value 학습 샘플 생성
- dataset builder
- model metadata registry
- model head-to-head evaluation
- tournament aggregation
- Elo 스타일 rating

이 시점에서 중요한 설계 결정은 **사용자의 실제 대국을 그대로 정답 데이터로 간주하지 않는다**는 것입니다.

사용자 수는 개인 학습에는 중요한 데이터지만, 현재 AI의 ground truth를 자동으로 정의하는 데이터와는 분리합니다.

---

## 9. 웹/API MVP 구축

도메인과 검색 기반이 만들어진 뒤 별도의 Python 웹 프레임워크 없이 표준 HTTP 서버로 작은 API 경계를 만들었습니다.

현재 주요 API:

- `GET /`
- `GET /api/health`
- `GET /api/state`
- `GET /api/record`
- `POST /api/reset`
- `POST /api/move`
- `POST /api/analyze/move`
- `POST /api/engine/move`

브라우저는 서버가 가진 authoritative state와 legal moves를 사용하며, 브라우저 자체가 장기 규칙을 판정하지 않습니다.

---

## 10. 브라우저 훈련기 구축

`index.html`을 dependency-free 브라우저 UI로 구성했습니다.

구현된 기능:

- 실제 9×10 장기판 표시
- 기물 선택
- 합법 목적지 표시
- 기본 배치 / 좌우 마상 교환 배치 선택
- 대국 초기화
- 사용자 착수
- 착수 분석
- 기준 엔진 수
- 코칭 결과 표시

현재 대국 모델은 **사용자 vs 기준 엔진**입니다.

사용자는 자신의 차례에 착수하고, 상대 차례에서는 기준 엔진이 수를 두는 구조입니다.

사용자가 양쪽 진영을 직접 조작하는 모드는 아직 없습니다.

---

## 11. 코칭 계층 도입

단순히 엔진 점수만 보여주는 것은 학습 도구로서 부족하기 때문에 별도의 `coaching.py` 계층을 추가했습니다.

현재 코칭 분류:

- 추천 수
- 괜찮은 대안
- 부정확한 수
- 큰 실수
- 분석 불가

초기에는 점수 변화량을 기준으로 보수적인 threshold를 사용했습니다.

현재 baseline이 기물 가치 + 기동성 중심의 단순 엔진이기 때문에, `blunder` 같은 과도하게 강한 표현을 피하고 **현재 기준 엔진 평가**라는 문맥을 유지하기로 했습니다.

---

## 12. 코칭 설명을 수의 특징까지 확장

점수 등급만으로는 사용자가 왜 그런 평가를 받았는지 알기 어렵기 때문에 코칭에 실제 착수 특징을 포함시키는 방향으로 확장했습니다.

현재 방향:

- 움직인 기물
- 잡은 기물
- 장군 여부
- 목적지 위험 여부
- 즉각적인 전술적 위험

이 단계에서 특히 **즉각적인 잡힘 위험(immediate capture risk)**을 포착하는 테스트를 추가했습니다.

이는 단순히 `score_delta`만 보는 것보다 실제 수의 이유를 설명할 수 있는 기반이 됩니다.

---

## 13. 테스트 강화

핵심 기능을 추가할 때마다 단위 테스트와 application boundary 테스트를 함께 추가했습니다.

특히 분석 계층에 대해 다음 항목을 검증했습니다.

- 추천 수 판정
- 초/한 관점 점수 정규화
- 불법 수 거부
- 실제 움직인 기물 식별
- 잡은 기물 식별
- 장군 여부
- 목적지 공격 여부
- 즉각적인 포획 위험
- 코칭 severity 분류
- API 상태 불변성
- 엔진 수 검증

초기 CI에서 실제 threshold 경계값 fixture 오류가 발견되었고, 테스트 fixture를 수정하여 통과시켰습니다.

---

## 14. Render 배포 과정과 문제 해결

GitHub `main` 브랜치와 Render를 연결해 자동 배포 환경을 구축했습니다.

초기에는 Render가 private GitHub 저장소에 접근할 수 없어 서비스 생성이 막혔습니다.

GitHub에서 Render가 접근할 수 있는 repository 범위를 확대하면서 정상적으로 서비스 생성이 가능해졌습니다.

현재 Render 서비스:

- 이름: `personal-ai-janggi-trainer`
- Runtime: Python
- Region: Singapore
- Plan: Free
- Branch: `main`
- Auto Deploy: Yes

서비스 URL:

`https://personal-ai-janggi-trainer.onrender.com`

---

## 15. 첫 배포 후 성능 문제 발견

첫 웹 배포는 정상적으로 `live` 상태가 되었지만, 실제 사용 시 응답이 느리고 일부 요청에서 `BrokenPipeError`가 발생했습니다.

Render 로그에서 다음 흐름이 확인되었습니다.

```text
/api/engine/move
/api/move
        ↓
BrokenPipeError
```

서버 프로세스가 죽은 것이 아니라, 엔진 계산이 오래 걸리는 동안 클라이언트 연결이 먼저 끊어진 상황으로 판단했습니다.

원인은 현재 검색 엔진이 각 후보 수를 평가할 때 장기 합법 수 계산을 반복 수행하는 구조와 무료 Render 인스턴스의 제한된 CPU 자원이 결합된 것으로 분석했습니다.

---

## 16. 웹용 검색 깊이 조정

응답성을 우선하기 위해 웹 애플리케이션에서 사용하는 검색 깊이를 `2 → 1`로 낮췄습니다.

중요한 설계 원칙은 `janggi/search.py`의 엔진 기본 설정을 변경한 것이 아니라, **웹 서비스에서 사용하는 설정만 낮춘 것**입니다.

따라서 향후 탐색 알고리즘과 평가 함수를 개선한 뒤 웹 검색 깊이를 다시 올릴 수 있습니다.

---

## 17. 파일 수정 실수와 복구

개발 중 `app.py`를 수정하는 과정에서 파일 전체가 의도치 않게 잘리는 사고가 한 번 발생했습니다.

즉시 GitHub의 현재 파일 내용을 다시 확인하고 원래 기능을 복구한 뒤 필요한 변경만 유지했습니다.

이후부터는 GitHub Contents API를 이용한 파일 수정에서 다음 원칙을 특히 강화했습니다.

- 항상 현재 SHA를 확인
- stale SHA 사용 금지
- 전체 파일을 덮어쓸 때 현재 내용을 먼저 확인
- 작은 수정은 최소 범위로 적용
- 배포 전 commit diff를 확인

이 사건은 앞으로의 자동 개발에서 **GitHub 파일 무결성 검증을 중요한 절차로 유지해야 한다는 근거**가 되었습니다.

---

## 18. UI 한국어화

프로토타입 화면에서 영어와 한글이 섞이는 문제를 확인하고 주요 UI 문자열을 한글로 통일했습니다.

변경 예:

- `Ready to begin` → `대국 준비`
- `Move coaching` → `착수 분석`
- `Reset session` → `대국 초기화`
- `Ask baseline engine` → `기준 엔진으로 수 두기`
- `Recommended` → `추천 수`
- `Acceptable alternative` → `괜찮은 대안`
- `Inaccuracy` → `부정확한 수`
- `Major mistake` → `큰 실수`

장기 기물 표시는 장기판 특성에 맞춰 한자 기물명을 사용합니다.

---

## 19. 현재 프로젝트 상태

현재 시스템의 전체 구조는 다음과 같습니다.

```text
장기 규칙 엔진
   ↓
Match / Record
   ↓
Engine Interface
   ↓
Negamax Search
   ↓
Move Analysis
   ↓
Coaching
   ↓
HTTP API
   ↓
Browser Trainer
   ↓
Render
```

현재까지 만들어진 것은 **MVP의 동작 가능한 골격**입니다.

아직 최종 AI 코치는 아닙니다.

특히 다음 항목은 앞으로의 핵심 개발 대상입니다.

- 더 정확한 전술/전략 코칭
- 복기 기능
- 반복 실수 추적
- 포지션 기반 훈련 문제 생성
- 사용자별 학습 데이터 축적
- 더 강한 검색 엔진
- 학습된 정책/가치 모델
- 장기적인 사용자 세션 및 데이터 저장

---

## 20. UI/모바일 후순위 결정

현재 사용자 피드백을 통해 다음 사항을 확인했습니다.

### 나중에 개선할 것

- 일반적으로 사용자가 아래쪽 진영에 위치하도록 장기판 방향 조정
- 모바일 환경 최적화
- 전체 UI 완성도 개선

현재는 기능 개발을 우선합니다.

```text
게임/학습 기능
   ↓
코칭 품질
   ↓
학습 데이터
   ↓
AI 성능
   ↓
UI / 모바일 최적화
```

---

## 21. 문서화 원칙

앞으로의 개발에서도 이 문서를 계속 누적 업데이트합니다.

새로운 기능을 구현할 때 다음 내용을 가능한 범위에서 기록합니다.

- 왜 이 기능을 만들었는가
- 어떤 설계 결정을 했는가
- 어떤 파일이 변경되었는가
- 테스트에서 무엇을 검증했는가
- 실제 배포에서 문제가 있었는가
- 문제가 있었다면 원인이 무엇이었는가
- 어떻게 수정했는가
- 어떤 부분을 다음 단계로 남겼는가

즉, 최종 코드만 남기는 것이 아니라 **개발 과정 자체를 프로젝트의 자산으로 보존**합니다.

---

## 22. 현재 기준 다음 개발 목표

현재 가장 중요한 다음 단계는 코칭을 단순한 점수 분류에서 실제 장기 훈련에 도움이 되는 **이유 설명형 코칭**으로 발전시키는 것입니다.

우선순위 후보:

1. 수의 전술적 특징을 더 정확히 추출
2. 잡힌 기물/위험 기물과 평가 변화의 연결
3. 장군과 위협의 설명 강화
4. 반복되는 실수 유형을 구조화
5. 특정 포지션을 다시 풀게 하는 훈련 모드 구축

장기적으로는 다음 목표로 이어집니다.

```text
착수
 ↓
분석
 ↓
설명
 ↓
실수 유형 기록
 ↓
약점 추적
 ↓
맞춤 훈련 생성
 ↓
학습
 ↓
재평가
```

이 루프가 이 프로젝트의 최종 제품 방향입니다.

---

## 부록 — 현재 주요 기술 결정

| 항목 | 현재 결정 | 이유 |
|---|---|---|
| Source of Truth | GitHub | 변경 이력과 코드 일관성 확보 |
| Backend | Python 표준 라이브러리 중심 | MVP 복잡도와 외부 의존성 최소화 |
| 규칙 권한 | `GameState` | 웹/UI/엔진의 규칙 중복 방지 |
| 검색 | Negamax + Alpha-Beta | 단순하고 검증 가능한 baseline |
| 평가 | Material + Mobility | 초기 구현 단순성 |
| 코칭 | 별도 `coaching.py` | 엔진 평가와 사용자 표현 분리 |
| 웹 | 표준 HTTP 서버 | MVP에서 프레임워크 의존성 최소화 |
| 배포 | Render | GitHub `main` 자동 배포 |
| 영속 저장 | 미구현 | MVP 이후 결정 |
| 인증 | 미구현 | MVP 이후 결정 |
| 모바일 | 후순위 | 기능 검증 우선 |
| 학습 모델 | 미구현 | 데이터/코칭 기반 확립 후 진행 |


## 32. Human-vs-AI match loop

### Requirement
사람이 초로 착수하면 AI가 한 수 자동 응수하고, 다시 사람 차례로 돌아오는 완결된 단일 대국 루프가 필요하다.

### Decision
브라우저가 `/api/analyze/move` → `/api/move` → `/api/engine/move`를 개별 조합하지 않고, 서버에 `/api/player/turn`을 추가해 사람 수 분석/착수와 AI 응수를 하나의 직렬화된 애플리케이션 턴으로 처리한다. AI 응수는 현재 baseline `NegamaxEngine`을 그대로 사용한다.

### Implementation
- Cho 플레이어 턴/ Han AI 턴을 서버에서 명시적으로 제한했다.
- `POST /api/player/turn`이 사람 수의 분석/코칭과 AI 응수 결과를 함께 반환한다.
- 기존 `/api/engine/move`는 자동 응답 실패 시 수동 복구 경로로 유지한다.
- 브라우저는 사람 수 후 AI 응수를 자동 실행하고, AI 응수가 가능하지 않으면 수동 복구 버튼을 제공한다.
- 일반적인 대국 되돌리기는 AI 응수와 직전 사람 수를 함께 제거해 이전 사람 차례를 복원한다.

### Boundary
이번 변경에서는 AI 검색 깊이와 평가함수 자체는 변경하지 않았다. 기능 목표는 '사람이 실제로 AI와 한 판을 끝까지 둘 수 있는가'이며, AI strength 개선은 별도 후속 단계다.

### Verification
- 사람 1수 + AI 1수의 서버-side turn contract 테스트 추가
- AI 턴 외부의 `/api/engine/move` 호출 거부 테스트 추가
- 브라우저의 자동 AI 응수 및 턴 복귀 contract 테스트 추가
- 기존 validation workflow로 compile/test 검증 예정


## 33. Baseline evaluation v2

### Requirement
현재 depth-2 baseline이 물질 차이와 기동력만으로 leaf position을 평가해, 동일한 material/mobility 범위 안에서 장기 형세 차이를 충분히 구분하지 못하는 문제가 있었다.

### Decision
탐색 깊이를 즉시 3으로 고정하지 않고 평가함수부터 강화한다. 말 가치 비율을 장기에서 일반적으로 쓰이는 순서에 맞춰 보정하고, 병의 전진/중앙성, 자기 궁성 내 사의 유지, 장군 압박을 작은 보정값으로 추가한다.

### Implementation
- 차/포/마/상/사/졸 값을 13/7/5/3/3/2 스케일로 재조정했다.
- 초/한 관점에 맞는 병 전진 보너스와 중앙 파일 보너스를 추가했다.
- 자기 궁성 내 사 유지 보너스를 추가했다.
- 현재 수가 장군을 주거나 받고 있는 상태를 bounded check pressure로 평가한다.
- 엔진 metadata version을 `2`로 올렸다.

### Boundary
법칙/합법수 생성/terminal 판정은 변경하지 않았다. 이번 단계는 search tree의 leaf 평가만 강화하며, 더 깊은 탐색과 quiescence는 별도 측정 후 진행한다.

### Verification
- 말 가치 계약 테스트 추가
- 전진한 중앙 졸 평가 테스트 추가
- 장군 압박 평가 테스트 추가
- 기존 검색 테스트와 deterministic benchmark를 통한 회귀 확인 예정


## 34. Bounded quiescence search

### Requirement
depth-2 search에서 마지막 평가 지점 직전에 잡기/장군 같은 forcing sequence가 시작되면, 단순 leaf evaluation 때문에 전술 교환을 놓칠 수 있다.

### Decision
일반 search depth는 그대로 유지하고 leaf에서 제한적인 quiescence search를 적용한다. 기본 `quiescence_depth=1`이며, quiet position은 stand-pat evaluation, check position은 legal evasion, 그 외 position은 capture/check만 연장한다.

### Implementation
- `SearchConfig.quiescence_depth`를 추가했다.
- leaf evaluation을 bounded `_quiescence()` 호출로 전환했다.
- 엔진 metadata version을 `3`으로 올렸다.
- PV 길이 계약을 `depth + quiescence_depth`까지 허용하도록 조정했다.
- 기본 depth는 2로 유지한다.

### Boundary
이번 변경은 depth 3 전체 탐색을 바로 강제하지 않는다. quiescence는 1-ply forcing extension일 뿐이며, 장기 전술을 완전히 해결하는 tactical solver로 간주하지 않는다.

### Verification
- quiescence depth 입력 검증 추가
- quiescence 활성화가 search node 수를 줄이지 않는지 regression test 추가
- deterministic search benchmark 재실행 예정


## 35. 2026-09-21 — Positional evaluation symmetry correction

### Finding

The current evaluation combined material, mobility, and positional terms, but the positional component was only computed for the side to move. This made the positional heuristic non-zero-sum: an opponent's advanced/central soldier or palace guard bonus did not reduce the evaluation from the mover's perspective.

### Decision

Correct the evaluation before increasing search depth. Search depth and engine protocol remain unchanged; the positional component now scores both sides symmetrically.

### Implementation

- `_positional_score()` now adds the side-to-move's bounded soldier/guard terms and subtracts the opponent's corresponding terms.
- Added a regression test for an opponent advanced center soldier.
- Added deterministic search baseline updates and improved benchmark failure reporting so all changed baselines are reported in one run.
- Updated `docs/SEARCH.md` and `docs/SEARCH_BENCHMARK_HISTORY.md`.

### Verification

GitHub Actions on the PR head confirmed:
- Python validation workflow passed on the initial code/test commit.
- Search benchmark executed the corrected evaluation across all current fixtures.
- New production node baselines are deterministic and were recorded from the GitHub Actions runner.
- The benchmark preserved minimax score equivalence across ordering variants.

### Boundary

This is an evaluation correctness/quality correction, not a claim that the AI is already stronger overall. The next strength step remains measured search-depth/tactical quality evaluation against deterministic fixtures and self-play.


## 36. 2026-09-23 — Browser session isolation

### Finding

The browser trainer previously routed every HTTP request to one process-wide `TrainerApplication`. As a result, all visitors shared the same match, undo history, review state, and training metrics.

### Decision

Introduce an opaque browser session identifier stored in an HttpOnly, SameSite cookie and resolve each request to its own in-memory `TrainerApplication`. Keep the existing domain, match, engine, and browser contracts unchanged.

### Implementation

- Added `TrainerSessionStore` with bounded in-memory session storage.
- Added per-browser `janggi_session` cookie handling in the dependency-free HTTP server.
- Routed stateful GET/POST endpoints through the session-specific `TrainerApplication`.
- Kept `/api/health` stateless so health checks do not create sessions.
- Added regression tests proving separate sessions have independent match state and cookie-based request routing.

### Boundary

This is session isolation, not persistent authentication. Sessions are process-local and disappear when the Render service restarts or a request is routed to a different service instance. Persistent accounts and shared session storage remain deferred to a later persistence layer.

### Verification

- Python compile and unit-test workflow covers session-store and request-cookie regressions.
- Existing Janggi domain, engine, coaching, training, and browser-contract tests remain unchanged apart from the new session coverage.


## 37. 2026-09-23 — Atomic human turn and API response recovery

### Finding

The browser gameplay flow still used two requests for one user turn: `/api/move` followed by `/api/engine/move`. If the second request received a non-JSON proxy/error response, the browser could stop after the human move while the server-side match had already advanced, causing client/server turn desynchronization. The browser's generic response parser also assumed every response body was JSON, producing `Unexpected token '<'` when an HTML error page was returned.

### Decision

Use `POST /api/player/turn` as the browser's single gameplay transaction. The application must roll back the human move when the AI response fails, and the browser must tolerate non-JSON responses and resynchronize from `GET /api/state` instead of attempting a blind retry.

### Implementation

- Browser human moves now call `/api/player/turn` once.
- `TrainerApplication.play_player_turn()` restores the original immutable match when any AI-response step fails.
- HTTP POST failures are returned as JSON when the application itself can produce the response.
- Browser response parsing now validates JSON before reading error payloads.
- Browser move failures trigger a state refresh to reconcile the UI with the server-side match.
- Added regression coverage for atomic rollback and the browser request contract.

### Boundary

This prevents partial application of a human-vs-AI turn and client-side JSON parsing crashes. It does not eliminate upstream proxy timeouts; after such a timeout, the browser reconciles with the authoritative server state rather than replaying the move.


## 38. 2026-09-23 — Immediate human move rendering and in-game feedback

### Requirement

The browser should show the learner's move immediately before the AI starts calculating, explain invalid destination clicks using the selected piece's movement rule, and surface turn-state events such as game start, check, response to check, and game termination.

### Decision

Use the existing low-level `/api/move` endpoint for the human move so the updated board can render before the separate `/api/engine/move` request begins. The server snapshot now exposes whether the side to move is in check. Browser messages derive from the pre-move and post-move snapshots and localized terminal status.

### Implementation

- Added `in_check` to session snapshots.
- Human move UI renders immediately after `/api/move` returns, then starts the AI calculation request.
- Added explicit messages for `장군`, `멍군`, and terminal outcomes including wins and draw reasons.
- Added a visible game-message area with `aria-live` for turn-state feedback.
- Added piece-specific invalid-move explanations for general, guard, elephant, horse, chariot, cannon, and soldier.
- Added regression coverage for the snapshot check-state field and browser feedback contracts.

### Boundary

The separate AI request remains recoverable: if it fails, the browser re-reads the authoritative server state instead of replaying the human move.


## 39. 2026-09-23 — Board overlay for turn-state feedback

### Requirement

AI search feedback and important match events should be visible directly on the board rather than only in the side panel. The human move must be visibly committed before the AI search begins.

### Decision

Keep the existing two-request browser flow so the human board update can render before the AI request, but force a browser paint boundary before starting `/api/engine/move`. Use a persistent board overlay during AI search and short-lived overlays for start/check/check-response/end events.

### Implementation

- Added an in-board overlay with a main message and optional secondary line.
- AI thinking overlay remains visible until the engine request resolves or errors.
- `장군` and `멍군` can be shown while the AI is thinking when relevant.
- Start and terminal messages display on the board for a short duration.
- Invalid moves continue to use piece-specific movement explanations.
- Added a regression test asserting human render and paint occur before the AI request.

### AI level clarification

AI levels intentionally differ by search budget: Lv.1 uses depth 1, mobility weight 0, and no quiescence; Lv.6 uses depth 3, mobility weight 2, quiescence depth 1, and an 800 ms search budget. The levels therefore search different amounts, but identical selected moves on a given position are still possible; a level configuration is not itself an empirical guarantee of different move choices or playing strength.



## 40. 2026-09-29 — Optimistic player move rendering regression guard

### Finding

The earlier immediate-human-move implementation rendered the authoritative board only after `POST /api/move` returned. Its regression test checked source-code ordering but did not guarantee that the browser had a visible player-move state before the AI request.

In practice, the browser could still present the human move and AI reply together depending on network timing and rendering scheduling.

### Decision

Keep `GameState` / `Match` authoritative and keep the two-request gameplay flow, but introduce a display-only `pendingPlayerMove` state.

The browser now:
1. validates the selected move against the server-provided legal-move snapshot,
2. renders the player move optimistically,
3. waits across an explicit two-frame paint boundary,
4. submits `POST /api/move`,
5. replaces the optimistic display with the authoritative server snapshot,
6. only then starts `POST /api/engine/move`.

On failure, the optimistic state is discarded and the browser re-synchronizes from `GET /api/state`.

### Regression protection

Added browser contract tests that require the optimistic render and paint boundary to occur before the `/api/move` request, and require `pendingPlayerMove` to remain display-only until the authoritative snapshot arrives.

This is a protected gameplay UX invariant, not an optional presentation detail.
