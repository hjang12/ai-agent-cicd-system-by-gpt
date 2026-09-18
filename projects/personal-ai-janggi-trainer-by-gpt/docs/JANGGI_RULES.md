# Janggi rules used by the core model

This document records the rules implemented in the first domain-core layer. The core keeps piece movement and board legality separate from future match policy such as tournament scoring, repetition decisions, and training-specific evaluation.

## Board and coordinates

- Board size: 9 files × 10 ranks (90 points).
- Coordinates in code are zero-based `(x, y)`.
- `y=0` is the top side's back rank and belongs to Cho (Blue).
- `y=9` is the bottom side's back rank and belongs to Han (Red).
- Cho moves first.
- Cho soldiers start at `y=3` and move toward increasing `y`; Han soldiers start at `y=6` and move toward decreasing `y`.

The coordinate convention is an implementation detail; users should not need to see it in the eventual UI.

## Initial position

Each side has 16 pieces: 1 General, 2 Guards, 2 Elephants, 2 Horses, 2 Chariots, 2 Cannons, and 5 Soldiers.

The fixed pieces are:

- General: center of the back rank (`e1` / `e10` in the top/bottom notation used by the reference rules).
- Guards: immediately left and right of the General on the back rank.
- Chariots: both corners of the back rank.
- Cannons: files `b` and `h`, one rank forward from the Soldier rank.
- Soldiers: files `a`, `c`, `e`, `g`, `i`, two ranks forward from the back rank.

Horse/Elephant positions have four common permutations: `classic`, `left`, `right`, and `both`. The domain model exposes these as `GameState.initial(setup=...)`.

## Piece movement

### General and Guard

They remain inside their own 3×3 palace. They move one point horizontally or vertically, and may also move one point diagonally along a marked palace diagonal.

### Chariot

Moves any distance horizontally or vertically until blocked. It can also move along the marked palace diagonals when it is on a palace-diagonal point.

### Horse

Moves one point orthogonally and then one point diagonally outward. The first orthogonal point must be empty; a piece there blocks the move.

### Elephant

Moves one orthogonal point and then two diagonal points outward, ending three files and two ranks away or two files and three ranks away. Both intermediate path points must be empty.

### Cannon

A cannon must jump exactly one non-cannon piece (the screen). The screen cannot itself be a cannon, and a cannon cannot capture another cannon. A cannon also cannot make an ordinary non-jumping move. Marked palace diagonals use the same one-screen rule.

### Soldier

A soldier moves forward or sideways. In the enemy palace it can additionally move one point along a forward marked palace diagonal. Janggi has no promotion.

## Legality and checks

- The domain layer does not model a "flying general" capture. Capturing the opposing General is rejected; positions are evaluated through attack/check state instead.
- A move that leaves the moving side's General in check is rejected.
- Passing (`한수쉼`) is represented explicitly as `Move.pass_move()` and is rejected while the side to move is in check.
- Two Generals facing one another on an open file are represented by `GameState.is_bikjang()` and are not treated as check by `is_in_check()`.
- Final match outcomes such as checkmate, consecutive-pass draw, repetition, perpetual-check restrictions, material scoring, and draw claims remain a separate policy layer.

## Domain-model boundary

`janggi/core.py` intentionally has no third-party dependency. It provides the authoritative board state and move legality foundation that future modules will build on:

`board state → game records → engine adapter → analysis → training data → self-play → model registry/rating → personal coaching`

External Janggi engines or model-training libraries are not embedded in this layer until their technical fit and licenses are reviewed.

## Rule references

The implementation was cross-checked against current public Janggi rule references for the 9×10 board, palace restrictions, initial setup, Horse/Elephant blocking, Cannon screens, Soldier movement, Cho-first turn order, pass, and bikjang handling:

- JanggiOnline — Korean Chess rules and setup: https://janggionline.com/how-to-play/
- Moddable Games — Janggi variant rules reference: https://rules.moddable.games/xiangqi/variants/janggi/

Tournament-specific rules may differ, so match-policy decisions should remain configurable rather than being hard-coded into piece movement.
