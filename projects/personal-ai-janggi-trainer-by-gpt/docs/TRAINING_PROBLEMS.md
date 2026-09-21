# Position Training Problems

`janggi/training_problems.py` converts current personal coaching-review evidence into bounded, non-persistent practice problems.

## Problem source

Only review entries with:

- severity `acceptable`, `inaccuracy`, or `major_mistake`;
- a valid normalized engine recommendation;
- a preserved pre-move `GameState`.

`recommended` and `unavailable` entries are not converted into problems.

## Problem contract

Each `PositionTrainingProblem` contains:

- a stable session-local `problem_id` based on the reviewed ply;
- the complete pre-move position and side to move;
- the original learner move;
- the current recommended target move;
- coaching severity and `reason_codes`;
- a learner-facing prompt, explanation, and next action.

The problem object validates that the target move is legal from the stored position.

## API behavior

`POST /api/training/problems` creates a bounded problem set from the current in-memory session. The default problem limit is 5 and the maximum is 20. The target move is omitted by default so the browser can present an actual problem. Trusted/internal callers may request `include_solution=true`.

`POST /api/training/answer` checks an attempted move against the regenerated current problem definition. It does not mutate `Match` or create persistent training state.

## Boundary

These problems are learning interactions, not ground-truth training labels. The recommended move comes from the existing normalized analysis contract, and a personal mistake does not become a model-training target merely because it generated a practice problem.

Persistence, per-user problem history, streaks, mastery tracking, and learned difficulty remain separate future concerns.