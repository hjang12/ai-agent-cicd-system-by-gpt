# Training Data Contract

`janggi/training.py` converts accepted completed game records into position/action/value examples.

## Sample shape

Each `TrainingExample` contains:

- `state` — the position before the played move.
- `move` — the action taken from that position.
- `outcome` — `WIN`, `DRAW`, or `LOSS` from the side-to-move perspective.
- `source` — the original record source.

`TrainingExample` validates that the action is a legal move from the stored pre-move state before the sample can exist. This keeps serialized or manually constructed datasets from silently containing impossible position/action pairs.

The serialized dataset uses `janggi-training-v1` and supports JSON round trips through `TrainingDataset.to_json()` / `from_json()`.

## Eligibility

The builder does not trust every record automatically. It runs the record through `RecordValidator` first.

Only records classified as `TrainingDisposition.CANDIDATE` produce examples. Under the current policy this means a replay-valid, complete record with a consistent result whose source is `curated-human` or `self-play`.

Personal and manual games remain useful for analysis/coaching but are not silently promoted to ground-truth training labels.

## Outcome perspective

The terminal result is first normalized to the Cho perspective and then converted per sample to the side-to-move perspective. A draw is always `0`; a win for the side to move is `1`; a loss is `-1`.

This makes the value target independent of which side happened to start the game and is directly compatible with a later value head or search-guided learner.

## Batch flow

Multiple records can be converted with `TrainingDatasetBuilder.build_many()`. The builder preserves input order and silently omits records that are not eligible for training.

The intended production flow is:

```text
self-play batch / curated human records
        ↓
RecordValidator
        ↓
TrainingDatasetBuilder
        ↓
position + action + value dataset
        ↓
future model training infrastructure
```

## Dataset boundaries

`TrainingDatasetBuilder` is intentionally a pure conversion layer. It does not train a model, shuffle samples, split train/validation sets, or choose a model architecture. Those concerns belong to the later model/data infrastructure layer.
## Self-play dataset artifact

The reproducible CLI `tools/generate_self_play_dataset.py` bridges validated self-play records into the existing `janggi-training-v1` JSON format.

Default collection settings are intentionally bounded and deterministic:

- 8 games
- 128 plies per game
- public AI level 4
- classic setup
- deterministic tie-breaking

The CLI also writes a sidecar summary containing the selected level/search profile, seeds, terminal vs unfinished games, training-eligible game count, and final example count. Unfinished games are never converted into value labels.

A manual GitHub Actions workflow, `.github/workflows/janggi-self-play-dataset.yml`, can generate larger artifacts without changing the production game path. Random fixed-seed tie-breaking is an explicit opt-in for dataset diversity experiments.
