# AI model architecture boundary

## Purpose

The search algorithm and the evaluation model must be replaceable independently.

The current production engine still uses the existing deterministic material/mobility/positional heuristic. This change does not alter public AI levels or promote a learned model. It creates the stable interface needed for a later self-play-trained value model.

## Boundary

NegamaxEngine accepts an optional value_model.

The model contract is:

- predict_cp(state: GameState) -> int
- the score is from state.turn's perspective;
- the score must remain strictly inside [-100000, 100000];
- the reserved mate-score range remains owned by the search/terminal logic;
- the model receives a history-free GameState snapshot because search evaluation caching is keyed by board contents and side-to-move.

When no value model is supplied, the existing heuristic evaluator is used exactly as before.

## Why this boundary exists

A future learned evaluator should be able to replace the hand-authored heuristic without changing:

- Janggi legality;
- Match and game records;
- alpha-beta/negamax search;
- transposition and move-ordering mechanisms;
- public six-level selection;
- browser/UI behavior;
- coaching and player-assessment interfaces.

This keeps model experiments isolated from gameplay infrastructure.

## Promotion policy

The interface alone is not evidence that a learned model is stronger.

A future model promotion must provide:

1. deterministic fixture correctness;
2. self-play comparison against the current heuristic/value version;
3. completed-game statistics with unfinished games kept separate;
4. regression coverage showing legal-move and terminal behavior remains authoritative;
5. recorded model metadata/version and reproducible parameters.

Until those checks are satisfied, the production engine remains on the existing heuristic evaluator.

## Dependency-free linear baseline

`janggi.value_model.LinearValueModel` is the first concrete implementation of the ValueModel boundary.

It uses a fixed, history-independent feature vector covering:

- material balance;
- per-piece balance;
- soldier progress;
- center control;
- legal-move mobility;
- general mobility;
- palace pressure;
- check pressure.

`LinearValueTrainer` fits the weights with deterministic ridge regression using only the standard library. This keeps the first learned-value experiment reproducible without coupling the project to NumPy, PyTorch, or another ML runtime.

The training target is side-to-move outcome:

- WIN → `+target_scale_cp`
- DRAW → `0`
- LOSS → `-target_scale_cp`

The default target scale is 3000 centipawn-like units and the default ridge regularization is 1.0.

## Training flow

`janggi-training-v1` JSON → `TrainingDataset.from_json()` → `LinearValueTrainer.fit()` → `LinearValueModel` JSON.

The manual workflow `.github/workflows/janggi-train-linear-value-model.yml` can generate self-play data and fit a candidate model in one reproducible run.

The candidate model is deliberately not registered as the production engine and is not wired into the public six-level ladder. A promotion decision requires deterministic fixture checks, head-to-head strength evidence against the current evaluator, and regression coverage for legality/terminal behavior.

## Candidate strength evaluation

`tools/benchmark_linear_value_model.py` compares a serialized linear candidate directly against the current heuristic evaluator using the same public AI search level, alternating colors through `HeadToHeadTournament`.

The manual training workflow now produces three artifacts together: validated self-play data, the trained linear model, and the candidate-vs-heuristic strength result. The strength result keeps unfinished games separate and only computes score/rating from completed games.

A single small benchmark is evidence that the pipeline works; it is not sufficient to promote the candidate. Larger repeated runs and deterministic fixture checks are still required before any production replacement.
