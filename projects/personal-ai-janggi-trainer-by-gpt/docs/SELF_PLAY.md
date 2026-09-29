# Self-Play Generation Contract

`janggi/self_play.py` defines the application boundary for generating engine-vs-engine Janggi records.

## Flow

```text
GameState
   ↓
Engine.choose_move()
   ↓
validate_engine_move()
   ↓
Match.play()
   ↓
terminal status / max plies
   ↓
GameRecord(source="self-play")
   ↓
RecordValidator
   ↓
training candidate or excluded
```

## `SelfPlayGenerator`

`SelfPlayGenerator` accepts a Cho engine and an optional Han engine. When the Han engine is omitted, the same engine instance is used for both sides.

Configuration includes:

- `setup` — one of the supported initial board variants.
- `rules` — the same `RuleSet` used by `Match` and `RecordValidator`.
- `max_plies` — a safety bound for generated games.

The generator never trusts an engine move directly. Every proposed move is checked by `validate_engine_move()` before it is applied through `Match.play()`.

## Completion and truncation

A game that reaches a `GameStatus` other than `PLAYING` is recorded with `result=<status.value>` and can become a training candidate when the record pipeline accepts it.

A game that reaches `max_plies` while still playing is recorded without a result. The pipeline classifies it as incomplete, so it is not eligible for outcome-dependent training data.

## Current search backend

`janggi/search.py` provides `NegamaxEngine`, a dependency-free depth-limited alpha-beta negamax backend. It uses the authoritative `GameState` for legality and a small deterministic material/mobility evaluation for move choice.

`SearchConfig` controls search depth and the mobility evaluation weight. `NegamaxEngine.analyze()` reports depth, visited nodes, score, best move, and principal variation through the existing `EngineAnalysis` contract.

This searcher is a baseline rather than a claim of strong tournament-level play. Its role is to make self-play executable with a real search process while keeping the engine boundary stable for later improvements or replacement by a stronger engine or trained model.

## `SelfPlayResult`

A generation result contains both:

- the immutable `GameRecord` that was produced; and
- the `RecordValidation` returned by the human-record pipeline.

Consumers should use `validation.training_eligible` rather than assuming that every generated game is suitable for training.
## Training-data generation CLI

`tools/generate_self_play_dataset.py` provides a reproducible bridge from the self-play boundary to the existing `janggi-training-v1` dataset format.

Example:

```text
PYTHONPATH=. python tools/generate_self_play_dataset.py --games 8 --max-plies 128 --level 4 --setup classic --seed 20260929
```

The command writes the raw training dataset plus a sidecar summary. Only records accepted as training-eligible by `RecordValidator` enter the dataset; incomplete games remain visible in the summary and are excluded from training labels.

For larger experiments, use the manual `.github/workflows/janggi-self-play-dataset.yml` workflow. The workflow is artifact-only and does not change the production engine or browser path.
