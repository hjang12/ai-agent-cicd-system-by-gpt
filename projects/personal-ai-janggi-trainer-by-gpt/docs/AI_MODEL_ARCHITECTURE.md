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
