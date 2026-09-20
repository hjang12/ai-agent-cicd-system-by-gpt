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

### `POST /api/move`

Applies one normal move through `Match.play`. Example:

```json
{"src":[0,3],"dst":[0,4]}
```

The domain model remains authoritative for legality; transport validation does not duplicate Janggi rules.

### `POST /api/undo`

Removes exactly the most recent move through `Match.undo` and returns the resulting match snapshot. The endpoint is rejected with HTTP 400 when the active match has no move history. Undo is one-ply and does not reconstruct match state in browser JavaScript.

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
    "reason_codes": ["capture"]
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

Runs the baseline `NegamaxEngine`, normalizes its analysis against the authoritative domain state, validates the selected move, and then applies it through `Match.play`. The returned principal variation therefore contains only moves that can be replayed legally from the position being analyzed.

## Session scope

The current server keeps one in-memory match per process. It is intentionally an MVP application boundary, not yet a persistent multi-user service. Authentication, databases, sessions, and concurrent-user isolation remain future application-layer concerns.

## Architectural rule

Do not move piece movement, check detection, terminal classification, or engine-legality decisions into HTTP handlers or browser JavaScript. The API should remain a transport/orchestration layer over the authoritative backend modules.
