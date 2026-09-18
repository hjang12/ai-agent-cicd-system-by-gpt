# Engine Adapter API

`janggi/engine.py` defines the boundary between the authoritative Janggi domain and any future move-search or AI backend.

## Design goal

The domain model owns legality. An engine proposes moves and analysis; it does not redefine board rules.

```text
GameState
   ↓
Engine.choose_move() / Engine.analyze()
   ↓
engine result
   ↓
validate against GameState
   ↓
Match.play()
```

## `EngineInfo`

Backend metadata exposed to the application:

- `name`
- optional `version`
- optional `author`

The application does not need to know whether the backend is a native executable, Python implementation, remote service, or trained model.

## `EngineAnalysis`

Backend-neutral analysis fields:

- `best_move`
- optional `score_cp`
- optional `depth`
- optional `nodes`
- `principal_variation`
- `perspective`

These fields are intentionally generic. Backend-specific telemetry should not leak into `core.py`.

Before an analysis is consumed by the trainer or coaching layer, `validate_engine_analysis()` normalizes it against the authoritative `GameState`. If a backend returns something other than `EngineAnalysis`, the boundary degrades it to an empty analysis for the current side to move. An invalid analysis perspective likewise degrades the result to an empty analysis. Invalid score/depth/node metadata is cleared individually. An illegal `best_move` is suppressed; a malformed or illegal `principal_variation` is removed; a variation without a usable `best_move` is removed; and a non-empty variation whose first move disagrees with `best_move` is also removed. This keeps presentation and coaching layers from treating malformed or internally inconsistent backend output as trustworthy move data.

## `Engine` protocol

Every backend implements:

```python
@property
def info(self) -> EngineInfo: ...

def choose_move(self, state: GameState) -> Move: ...

def analyze(self, state: GameState) -> EngineAnalysis: ...
```

`choose_move()` must return a legal move for the supplied state. The application still validates the result through `validate_engine_move()` instead of trusting a backend blindly. Engine analysis is normalized through `validate_engine_analysis()` before it crosses into higher-level presentation or coaching.

## Test backend

`FirstLegalEngine` is a deterministic integration-test backend. It intentionally has no playing strength and no external dependency. Its purpose is to prove the application/engine boundary before a real engine is selected.

It must not be presented as the product's AI opponent.

## Future backend requirements

A real engine adapter should be evaluated separately for:

1. Janggi rule correctness, including palace and cannon behavior.
2. Strength and performance.
3. Move/position interoperability.
4. Analysis output quality.
5. Process or API lifecycle management.
6. License compatibility with this project.
7. Training and self-play integration capability.

The concrete engine selection remains intentionally deferred until those requirements are validated.
