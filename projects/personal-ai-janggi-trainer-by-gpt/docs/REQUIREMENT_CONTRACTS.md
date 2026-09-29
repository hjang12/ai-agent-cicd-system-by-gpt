# Requirement Contracts

이 문서는 사용자가 한 번 요청하고 구현·검증이 완료된 동작 중, 후속 개발에서도 **조용히 원복하면 안 되는 제품 요구사항**을 관리한다.

기계 판독 원본은 [`requirement_contracts.json`](./requirement_contracts.json)이다.

## Lifecycle

`ACTIVE` Contract는 현재 유효한 제품 계약이다.

후속 작업은 먼저 관련 Contract를 확인하고, 구현을 변경하더라도 Contract의 관찰 가능한 동작과 회귀 테스트를 유지해야 한다.

기존 Contract와 충돌하는 새 요구사항이 생긴 경우:

1. 기존 Contract를 임의로 원복하지 않는다.
2. 충돌 관계와 영향 범위를 사용자에게 보고한다.
3. 사용자 결정 후 기존 Contract를 `SUPERSEDED` 또는 `RETIRED`로 변경한다.
4. 변경 이유, 구현, 검증 결과를 `DEVELOPMENT_HISTORY.md`에 남긴다.
5. Pull Request에서 Contract 정의나 회귀 테스트 자체를 의도적으로 변경하는 경우 PR 설명에 `CONTRACT-CHANGE: <ID>`를 명시한다.

## Active Contracts

### UX-001 — Human move is visibly rendered before AI calculation begins

**Requirement**

사용자가 합법적인 수를 선택하면 AI 계산이 시작되기 전에 사용자 수가 장기판에 먼저 보이는 상태가 되어야 한다.

**Protection**

- Browser optimistic presentation state: `pendingPlayerMove`
- Authoritative server state remains `GameState / Match`
- Explicit paint boundary before the player-move network transaction / AI response sequence
- Regression tests remain in `tests/test_app.py`

**Change rule**

이 동작을 없애거나 다시 "AI 응답까지 한 번에 보이는 방식"으로 바꾸는 것은 단순 리팩터링이 아니라 Contract 변경이다. 새로운 요구사항 때문에 변경이 필요하면 현재 Contract와 충돌한다고 사용자에게 보고하고, 사용자 결정 이후 변경한다.

### AI-001 — Six public AI levels remain selectable with distinct search profiles

**Requirement**

브라우저 트레이너는 6개 AI 레벨을 계속 제공해야 하며, 각 레벨의 문서화된 검색 프로파일은 실질적으로 구분되어야 한다. 실제 대국 전력의 순서는 설정만으로 간주하지 않고 별도 calibration benchmark로 검증한다.

**Protection**

- Public level configuration: `janggi/ai_level.py`
- AI level regression coverage: `tests/test_ai_level.py`
- Level methodology/evidence: `docs/AI_LEVELS.md`, `tools/benchmark_ai_levels.py`

**Change rule**

레벨 수를 줄이거나 검색 프로파일 차이를 제거하려면 Contract 변경으로 취급하고 사용자에게 변경 이유와 영향을 보고한다.

## 운영 원칙

- 보호 대상은 구현 코드 전체가 아니라 **사용자 관찰 가능 동작 + 그 동작을 보호하는 회귀 테스트**다.
- 보호된 구현 파일을 수정하는 것 자체는 금지하지 않는다. 테스트가 Contract를 계속 증명하면 내부 구현 교체는 허용한다.
- 회귀 테스트 삭제/약화, Contract Registry 변경, Contract 상태 변경은 명시적 변경으로 취급한다.
- CI가 보호 경로 변경을 표시해도 그것만으로 동작 변경이라고 단정하지 않는다. 실제 동작 변경 여부는 테스트와 변경 의도를 함께 판단한다.
