# Coaching Rules

## Purpose

`janggi/coaching.py` converts normalized `MoveAnalysis` data into conservative learner-facing feedback. It is an explanatory layer: it should help the player understand why a move was recommended, acceptable, inaccurate, or tactically risky without claiming more certainty than the underlying analysis supports.

The coaching layer does not determine move legality, search strength, or tactical truth. Those responsibilities remain with the domain and analysis/search layers.

## Severity Rules

The current severity classification is stable and score-based except for the explicit hanging-piece override.

- `RECOMMENDED`: the analyzed move is the current engine recommendation.
- `ACCEPTABLE`: the move is not the recommendation, but score loss is at least `-25` centipawns-equivalent.
- `INACCURACY`: score loss is below `-25` and at least `-150`.
- `MAJOR_MISTAKE`: score loss is below `-150`.
- `MAJOR_MISTAKE`: `HANGING_PIECE` overrides the numeric score classification, because the immediate tactical risk is the primary coaching issue.
- `IMMEDIATE_CAPTURE` does not override numeric severity; it changes the explanation so the learner is prompted to inspect the opponent's capture and possible recapture sequence.
- `UNAVAILABLE`: there is no recommendation to compare against, or no score delta is available where one is required.

The constants that define the current score thresholds are `ACCEPTABLE_DELTA_CP = -25` and `INACCURACY_DELTA_CP = -150` in `janggi/coaching.py`.

## Explanation Rules

The message has two conceptual parts: move facts detected by analysis and an action-oriented explanation.

### Recommended moves

The base explanation distinguishes the most useful immediate features:

- Capture + check: explain that the move captures and gives check at the same time, forcing a response.
- Capture: explain that the move matches the recommendation and remind the learner to inspect the opponent's next counterattack.
- Check: explain that the move matches the recommendation and constrains the opponent's available response.
- Otherwise: explain that the move matches the current recommendation.

### Acceptable alternatives

An acceptable move is described as a viable alternative rather than as a failure. The learner is prompted to compare the move with the recommendation and identify the difference in purpose or continuation.

### Inaccuracies

An inaccurate move is described relative to the recommendation. The learner is prompted to preserve the intended purpose while checking one more opponent reply for counterplay.

### Major mistakes

For score-based major mistakes, the explanation points the learner toward immediate counterplay instead of asserting a forced tactical result.

For hanging pieces, the explanation explicitly directs attention to the opponent's available capture and protecting the moved piece.

For immediate-capture risk, the explanation asks whether the intended exchange is sound by checking whether the learner can recapture after the opponent takes the moved piece.

### Tactical motifs

The current bounded `DOUBLE_ATTACK` signal is an explanatory warning. When present, coaching may state that the opponent can attack two pieces on the next move. This wording must not be treated as proof of a forced win, and the motif does not alter score-based severity.

## Structured learner action

Each `CoachingInsight` also exposes a `next_action` field containing one concise learner action that can be rendered independently from the longer explanation message.

Examples include:

- recommended capture → inspect the opponent's next counterattack;
- recommended check → inspect the opponent's available response;
- acceptable alternative → compare purpose and continuation with the recommendation;
- inaccuracy → look one reply deeper for counterplay;
- hanging piece → inspect the capture and a protecting move;
- immediate-capture risk → verify whether the piece can be recaptured;
- unavailable analysis → wait for a position with a usable comparison.

This field is deliberately generated in the coaching layer rather than inferred by the browser UI. Browser presentation can therefore display the action without parsing or duplicating coaching rules.

## Message Construction Invariant

`_feature_message()` may combine factual features from `MoveAnalysis`, including moved piece, captured piece, check status, destination attack, hanging-piece risk, and the bounded double-attack warning. It must not independently reimplement Janggi legality or search logic.

This separation is intentional:

```text
GameState / search / analysis
        ↓
   MoveAnalysis facts
        ↓
   coaching.py
        ↓
 severity + message + next_action
        ↓
 learner-facing explanation
```

## Non-goals

The coaching layer does not:

- invent tactical motifs that are not present in `MoveAnalysis`;
- change the engine recommendation;
- change search evaluation or node ordering;
- turn heuristic warnings into claims of forced wins or losses;
- duplicate domain move-legality rules;
- introduce persistence, accounts, or model-training policy.

## API Contract

`POST /api/analyze/move` returns the coaching object with:

- `severity`
- `message`
- `score_delta_cp`
- `next_action`

`next_action` is presentation-ready guidance but remains derived exclusively from the normalized analysis facts and existing coaching rules.

## Test Coverage

`tests/test_coaching.py` covers the current contract, including:

- recommended moves;
- recommended capture + check, capture, and check explanations;
- acceptable alternatives and comparison guidance;
- inaccuracy and counterplay guidance;
- score-based major mistakes;
- hanging-piece override and protection guidance;
- immediate-capture explanation with recapture guidance;
- combination of move facts in one explanation;
- bounded double-attack explanation without severity changes;
- unavailable analysis when no recommendation exists;
- structured `next_action` guidance for the above coaching categories.

`tests/test_app.py` verifies that the HTTP-facing analysis contract exposes `next_action` as a non-empty coaching field.

When coaching wording or learner-action guidance changes, update this document and the focused unit tests together so the repository remains the source of truth for the learner-feedback contract.
