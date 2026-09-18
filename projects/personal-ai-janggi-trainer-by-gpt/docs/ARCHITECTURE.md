# Architecture

## Purpose

The backend is structured so the Janggi rules remain authoritative and higher-level product features can evolve without coupling the domain model to a particular UI, API framework, search implementation, or future machine-learning model.

## Module boundaries

```text
GameState / Move / Piece
        |
        v
      Match
        |
        +--------------------+
        |                    |
        v                    v
     Engine              Record / Pipeline
        |                    |
        v                    v
     Search             Training Dataset
        |
        v
   Self-play
        |
        v
 Evaluation / Tournament / Rating
```

### Domain: `janggi/core.py`

`GameState`, `Move`, `Piece`, and movement/legality rules are the single source of truth for board state and legal play. Other modules should ask the domain whether a move is legal rather than reimplementing movement rules.

### Match orchestration: `janggi/match.py`

`Match` owns an in-progress game, applies legal moves, tracks repetition/pass state, and derives terminal status. It is the boundary between a raw game state and a played match.

### Engine boundary: `janggi/engine.py`

An engine proposes a move or analysis. The domain remains authoritative: callers validate engine output before applying it through `Match`/`GameState`. This allows the current baseline search to be replaced later without changing game-rule ownership.

### Search: `janggi/search.py`

`NegamaxEngine` is the current deterministic baseline search. It is intentionally separated from the domain so search quality can evolve independently of rule correctness.

### Records and validation: `janggi/record.py`, `janggi/pipeline.py`

Records are portable game data. The validation pipeline distinguishes structural validity, replay validity, completeness, source provenance, and training eligibility. A human or personal record is not silently promoted to ground truth.

Serialized state may optionally include the setup identifier. When setup is known, deserialization validates that the recorded history replays to the serialized board and turn. Legacy state payloads without setup remain readable, but their history cannot be independently validated against a known initial position.

### Training: `janggi/training.py`

Training examples are produced only from records accepted by the validation pipeline. Outcome labels are normalized to the side-to-move perspective so model training can use a consistent target convention.

### Model metadata: `janggi/model.py`

`ModelSpec` and `ModelRegistry` store stable model identity and metadata only. Engine instances are not stored in the registry. This keeps model selection separate from execution and search implementation.

### Evaluation and rating: `janggi/evaluation.py`, `janggi/tournament.py`, `janggi/rating.py`

Evaluation games measure model-versus-model results. Tournaments aggregate completed games, while rating updates are kept as a separate concern. Unfinished games do not become wins, losses, or draws merely because a game was capped.

## Data flow

### Interactive play

```text
Client / future API
      |
      v
   Match.play
      |
      v
GameState.apply
      |
      v
 terminal status
```

### Engine play

```text
GameState
   |
   v
Engine.analyze_position / choose_move
   |
   v
validate_engine_move
   |
   v
Match.play
```

### Training data

```text
GameRecord
   |
   v
RecordValidator
   |
   +--> rejected / analysis-only
   |
   v
TrainingDatasetBuilder
   |
   v
TrainingExample
```

### Model evaluation

```text
ModelSpec
   |
   v
Engine instance / adapter
   |
   v
EvaluationGame / HeadToHeadTournament
   |
   v
results -> RatingUpdate
```

## Persistence contract

The current implementation uses explicit, versioned JSON payload identifiers such as `janggi-record-v1`, `janggi-state-v1`, and `janggi-training-v1`. New fields should prefer backward-compatible additions rather than silently changing the meaning of existing fields.

For future API/database work, keep three concepts distinct:

1. A **position snapshot**: board plus side to move.
2. A **game record**: setup, move history, source, and result metadata.
3. A **training example**: a pre-move position, played move, label, provenance, and eventually model/data lineage.

Keeping these concepts separate prevents UI state, replay history, and training provenance from becoming one overloaded persistence object.

## Future extension points

Web/API, persistent storage, authentication, model downloads, and trained ML models are intentionally outside the current core. They should depend on these stable backend boundaries rather than moving rule logic into transport or UI modules.

The next application layer should therefore expose domain and orchestration services without bypassing `GameState` legality checks.
