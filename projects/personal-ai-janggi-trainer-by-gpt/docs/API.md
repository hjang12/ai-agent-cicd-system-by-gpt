# Web API

The current application boundary is a small dependency-free HTTP service in `app.py`. It keeps the browser transport layer outside the Janggi domain model and delegates state changes to `Match`.

## Runtime

Start with:

```text
python app.py
```

The server listens to `0.0.0.0` and uses the `PORT` environment variable when provided, defaulting to `8000`.

## Endpoints

### `GET /`

Serves the dependency-free browser trainer shell from `index.html`.

### `GET /api/health`

Returns a liveness payload:

```json
{"status":"ok"}
```

### `GET /api/state`

Returns the current match status, setup, serialized state, and currently legal moves. The serialized state includes the complete move history used by the browser to determine whether undo is available.

### `GET /api/record`

Returns the current in-memory session as a `janggi-record-v1` game record, including setup, result, source, and played moves.

### `POST /api/reset`

Resets the in-memory session. Optional JSON body:

```json
{"setup":"classic"}
```

Supported setups are `classic`, `left`, `right`, and `both`.

### `POST /api/player/turn`

Applies one human (Cho) move, runs the existing move-analysis/coaching pipeline, then automatically asks the baseline AI (Han) for one legal response when the game remains in progress. The endpoint returns both player analysis/coaching and the resulting AI analysis together with the post-turn snapshot.

Example:

```json
{"src":[0,3],"dst":[0,4]}
```

This is the primary human-vs-AI game-loop endpoint. The backend owns turn authority, so a human move is rejected when it is the AI's turn.

### `POST /api/move`

Applies one human (Cho) move through `Match.play`. The endpoint is retained as a low-level compatibility path; the browser uses `/api/player/turn` so the AI response is part of the same server-side turn.

### `POST /api/undo`

Restores the previous human decision point. In a normal human-vs-AI round, this removes the AI reply and the immediately preceding human move together. The endpoint is rejected with HTTP 400 when the active match has no move history.

### `POST /api/analyze/move`

Analyzes a legal move against the current baseline engine without mutating the active match. Example:

```json
{"src":[0,3],"dst":[0,4]}
```

The response contains the raw move analysis plus a conservative learner-facing `coaching` object:

```json
{
  "coaching": {
    "severity": "recommended",
    "message": "좋은 수입니다. 현재 기준 엔진 추천수와 같습니다.",
    "score_delta_cp": 0,
    "next_action": "상대의 다음 반격을 확인하세요.",
    "reason_codes": []
  },
  "analysis": {
    "tactical_risk": "none"
  }
}
```

Possible `severity` values are `recommended`, `acceptable`, `inaccuracy`, `major_mistake`, and `unavailable`. The labels are presentation-layer guidance derived from the current baseline material/mobility score; they are intentionally conservative and are not equivalent to engine-grade tactical labels.

The move analysis also reports `tactical_risk`:

- `none` — no immediate capture risk was detected.
- `immediate_capture` — the opponent can immediately capture the moved piece, but at least one immediate legal recapture exists.
- `hanging_piece` — the opponent can immediately capture the moved piece and the mover has no immediate legal recapture after that capture.

This tactical signal is deliberately shallow and domain-derived. It does not claim that an engine search has proven the position globally losing. Stronger multi-ply motif detection belongs in a future analysis layer.

The coaching object also includes stable machine-readable `reason_codes` for future aggregation without parsing the learner-facing message text. Current values are `hanging_piece`, `immediate_capture`, `double_attack`, `score_deviation`, `capture`, and `check`. Multiple codes may be present on one move.
 
The response also includes the played move, current recommendation, score before/after, score delta, search metadata, and the unchanged current snapshot. Engine best-move recommendations and principal variations are normalized against the authoritative domain state before they are exposed through this analysis path; malformed move data is suppressed rather than surfaced as valid guidance.

### `POST /api/engine/move`

Runs the baseline `NegamaxEngine`, normalizes its analysis against the authoritative domain state, validates the selected move, and then applies it through `Match.play`. It is restricted to the AI (Han) turn and is primarily a recovery/manual path because the normal browser flow already calls `/api/player/turn`.

### `POST /api/review`

Reviews the current in-memory session without changing the active match. The application treats Cho as the learner side and analyzes up to the requested number of the learner's most recent moves.

Optional JSON body:

```json
{"limit":20}
```

The limit defaults to 20 and is bounded to 60. The response aggregates stable coaching `reason_codes` and severity counts, and includes one compact entry per reviewed learner move with the move, recommendation, score delta, explanation, next action, and reason codes.

```json
{
  "total_moves": 12,
  "reviewed_moves": 6,
  "skipped_moves": 0,
  "reason_counts": {
    "score_deviation": 4,
    "hanging_piece": 2
  },
  "severity_counts": {
    "recommended": 2,
    "acceptable": 1,
    "inaccuracy": 1,
    "major_mistake": 2
  },
  "entries": []
}
```

Review is intentionally on-demand and non-persistent. It replays the authoritative `GameRecord` and therefore preserves the same legality boundary as the normal game flow.

### `POST /api/training/problems`

Builds bounded, non-persistent position-training problems from the current learner-side review.

Optional JSON body:

```json
{"review_limit":20,"problem_limit":5}
```

The endpoint returns each problem's complete pre-move position, legal moves, original learner move, conservative severity/reason codes, prompt, explanation, and next action. The service considers up to 20 eligible review-derived problems and, using the current ephemeral training metrics, prioritizes repeatedly missed problem ids first and then reason codes with observed mistakes and lower session accuracy. When there are no observed reason-specific mistakes, the recent-first order is preserved. The recommended target move is intentionally omitted by default so the browser can present the position as a problem instead of immediately revealing the answer.

Set `include_solution` to `true` for trusted/internal consumers that need the target move. The response also includes `priority_reason_codes` and `priority_problem_ids`. The former lists reasons ordered from the lowest observed session accuracy among reasons with at least one mistake; the latter lists problem ids with repeated incorrect answers, ordered by observed incorrect count.

### `GET /api/training/metrics`

Returns the current in-memory training-session metrics without changing the active match.

```json
{
  "attempts": 4,
  "correct": 2,
  "incorrect": 2,
  "unique_problems": 3,
  "accuracy": 0.5,
  "problem_attempts": {"ply-7": 3, "ply-9": 1},
  "problem_incorrect": {"ply-7": 2},
  "reason_attempts": {
    "hanging_piece": 2,
    "score_deviation": 4
  },
  "reason_correct": {
    "hanging_piece": 1,
    "score_deviation": 2
  }
}
```

`attempts` counts legal training answers submitted. Metrics reset with `POST /api/reset` and are never persisted.

### `POST /api/training/answer`

Checks one attempted move against a generated problem without mutating the active match.

Request:

```json
{
  "problem_id":"ply-7",
  "src":[0,3],
  "dst":[0,4]
}
```

The response reports whether the move was legal and matched the current recommendation, and returns the target move and coaching guidance. This is an in-memory learning interaction; no training score, account state, or persistent history is created.

Training problems are generated only from reviewed moves that are `acceptable`, `inaccuracy`, or `major_mistake` and have a valid engine recommendation. `recommended` and `unavailable` review entries are not converted into problems.

## Session scope

The current server keeps one in-memory match per process. It is intentionally an MVP application boundary, not yet a persistent multi-user service. Authentication, databases, sessions, and concurrent-user isolation remain future application-layer concerns.

## Architectural rule

Do not move piece movement, check detection, terminal classification, or engine-legality decisions into HTTP handlers or browser JavaScript. The API should remain a transport/orchestration layer over the authoritative backend modules.
