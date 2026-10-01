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

### UX-002 — Selected piece and AI thinking state are visibly indicated

**Requirement**

사용자가 합법적인 기물을 선택하면 선택된 칸이 명확한 시각적 표시를 가져야 하고 이동 가능한 칸도 구분되어야 합니다. 사용자의 수가 제출된 뒤에는 AI 응수가 끝나거나 오류 상태가 복구될 때까지 장기판 위에 명확한 **AI 생각 중** 오버레이가 표시되어야 합니다.

**Protection**

- Selected cell styling: `.cell.selected`
- Legal destination styling: `.cell.legal`
- Pending move state: `pendingPlayerMove`
- Board thinking overlay: `.board-message` / `.board-message.thinking`
- Regression tests remain in `tests/test_app.py`

**Change rule**

이 피드백을 제거하거나 AI 계산 중 상태를 숨기는 것은 단순 리팩터링이 아니라 Contract 변경입니다. 새로운 요구사항 때문에 변경이 필요하면 현재 Contract와 충돌한다고 사용자에게 보고하고, 사용자 결정 이후 변경합니다.

### UX-003 — Trainer is a scroll-free single-screen web app

**Requirement**

장기 훈련기의 주요 사용 화면은 브라우저 viewport 안에서 페이지 스크롤 없이 동작해야 합니다. 장기판을 시각적 중심으로 두고, 설정·실력 평가·착수 분석·복기·훈련은 고정 높이의 앱 영역 안에서 함께 접근할 수 있어야 합니다.

**Protection**

- Viewport shell: `height:100dvh`
- Page overflow contract: `html,body` use `overflow:hidden`
- Layout contract: fixed application grid with `min-height:0`
- Regression test: `tests/test_app.py::test_browser_single_screen_layout_contract`

**Change rule**

스크롤 기반의 일반 페이지로 되돌리거나 대국 화면과 학습 기능을 별도 긴 페이지로 분리하는 변경은 단순 리팩터링이 아니라 Contract 변경입니다.

### UX-004 — Game-first layout does not let auxiliary surfaces cover the board

**Requirement**

일반 대국 화면에서는 장기판·대국 상태·최소 행동이 주된 표면이어야 합니다. 설정·분석·복기·훈련은 명시적인 버튼으로만 열고, 열려 있을 때도 앱 레이아웃 공간을 사용하여 장기판을 가리는 overlay로 동작하지 않아야 합니다.

**Protection**

- Game-stage/flexible board layout in index.html
- Explicit settings/learning toggles
- Desktop drawer columns and mobile drawer rows consume layout space
- Regression tests remain in tests/test_app.py

**Change rule**

보조 화면이 다시 상시 노출되거나, drawer를 통해 장기판을 가리는 overlay 구조로 되돌리는 변경은 단순 리팩터링이 아니라 Contract 변경입니다.

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
