# Current Status

## Governance

- Common Governance Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Governance Version: `1.0.0`
- Governance status: active baseline on `main`
- Project context entrypoint: `AGENT_START.md`

## Product

- Project: Personal AI Janggi Trainer
- Canonical Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Project Path: `projects/personal-ai-janggi-trainer-by-gpt/`
- Default branch: `main`
- Primary user: one self-directed Janggi learner using a desktop browser
- Current priority: complete the human-vs-AI match loop first, then improve baseline AI strength while preserving clean engine/evaluation boundaries

## Implemented Capability

- Dependency-free Janggi domain and board representation
- Standard initial setup variants
- Piece movement and move legality
- Check/bikjang detection and pass handling
- Position keys and move history
- Game records, JSON serialization, replay, match status, and configurable match-policy rules
- Match undo that restores the immediately previous immutable state while preserving setup and rule policy
- Backend-neutral engine protocol and validation
- Engine-analysis normalization that suppresses illegal recommended moves, malformed principal variations, variations inconsistent with the recommended move, invalid metadata, and non-`EngineAnalysis` backend output
- Move/position analysis normalization
- Conservative learner-facing coaching classification
- Domain-level tactical risk detection for immediate captures and hanging pieces
- Tactical-risk-aware learner coaching messages with separate tactical and score-based interpretation
- Action-oriented coaching explanations for captures, checks, alternative moves, and counterplay review
- Structured coaching `next_action` guidance for browser/UI presentation without message parsing
- Stable coaching `reason_codes` for machine-readable tactical, capture/check, and score-deviation signals without message parsing
- Bounded on-demand session review that replays the current record, preserves pre-move states, analyzes recent learner-side moves, and aggregates reason/severity counts without persistence
- Bounded position-training problem generation from non-recommended review entries, with browser answer checking and no persistence
- Ephemeral training-session metrics for attempts, correctness, unique problems, overall accuracy, and reason-specific attempt/correctness exposure
- Session-local adaptive training problem selection that prioritizes repeated incorrect problem attempts, bounds their share when other candidates exist, then uses observed reason-specific mistakes and lower accuracy, with recent-first fallback
- Representative tactical regression fixtures for clean captures, protected exchanges, hanging pieces, non-immediate threats, and bounded double-attack threats
- Bounded `double_attack` tactical motif signal kept separate from score-based severity
- Human-record validation and training-data eligibility pipeline
- Dependency-free negamax/alpha-beta search baseline with evaluation v3 (evaluation v2 plus bounded quiescence search at the leaf horizon)
- Capture-first and checking-move ordering, exact-result transposition caching, per-analysis evaluation caching, per-analysis check caching, and per-analysis legal-move caching in baseline search
- History-independent checkmate scoring consistent with the search position-key semantics
- Deterministic search-ordering benchmark comparing production forcing-move ordering with a coordinate-only reference
- Deterministic legal-move generation benchmark comparing cached and uncached search work
- Expanded benchmark fixtures covering a mixed-material midgame and a reduced-material endgame position
- Deterministic production node-count baselines now include the new midgame/endgame fixtures
- Persistent search benchmark history in `docs/SEARCH_BENCHMARK_HISTORY.md`
- Self-play generation
- Position/action/value training examples and dataset builder
- Model metadata registry
- Head-to-head evaluation, tournament aggregation, and Elo-style rating primitives
- Dependency-free browser trainer and HTTP API
- Per-browser in-memory session isolation using an opaque HttpOnly SameSite cookie, so separate browser sessions no longer share the same `Match` or training state
- Browser analysis panel shows tactical risk, bounded tactical warnings, recommendation principal variation, and structured next-action coaching; principal variations use learner-facing board notation (`a1`–`i10`) with numbered plies and side labels, terminal results are localized, and turn handoff is explicit in the heading
- Browser engine-move result also shows the engine principal variation, normalized evaluation score, search depth, and visited-node count as learning aids
- Browser match flow renders the human move immediately through `/api/move`, then starts the AI calculation through `/api/engine/move`; the UI exposes check-state feedback (`장군`/`멍군`) and localized terminal results. The previously available `/api/player/turn` remains an atomic server-side transaction for callers that need the combined turn contract. Browser requests validate JSON responses and resynchronize from `/api/state` after request-format/server errors. Undo restores the previous human decision point by removing the AI response plus the preceding human move when applicable

## Web/API

- `GET /` — browser trainer shell
- `GET /api/health` — service health
- `GET /api/state` — current browser-session match snapshot and legal moves
- `GET /api/record` — current browser-session record
- `POST /api/reset` — reset the current browser session's match/setup
- `POST /api/move` — low-level player move compatibility endpoint
- `POST /api/player/turn` — apply one human move and automatically apply one baseline AI response
- `POST /api/undo` — restore the previous human decision point, normally undoing the AI reply plus the preceding human move
- `POST /api/analyze/move` — analyze a legal move without mutating the active match
- `POST /api/engine/move` — analyze, validate, and apply a baseline engine move
- `POST /api/review` — review recent learner-side moves from the current in-memory record and aggregate coaching signals
- `POST /api/training/problems` — generate bounded non-persistent position-training problems from the current review, with session-local reason-specific adaptive prioritization
- `POST /api/training/answer` — check a training attempt against the current problem definition without changing the match
- `GET /api/training/metrics` — read current non-persistent training-session metrics
- Move analysis API includes `tactical_risk` (`none`, `immediate_capture`, `hanging_piece`) and `tactical_motifs` (currently `double_attack` when detected)
- Move coaching API includes `severity`, `message`, `score_delta_cp`, presentation-ready `next_action`, and stable `reason_codes` for future repeated-mistake aggregation
- Engine move analysis includes principal variation data after authoritative legality normalization
- Position-training problems preserve the original pre-move state, hide the target move by default, and reuse the existing coaching reason/severity contract
- Training metrics reset with the match and are never promoted to persistent user or model-training data; problem-level repeated-mistake counts and reason-specific accuracy are derived from the same ephemeral counts, and adaptive selection uses those counts only for the current session

## CI/CD

GitHub Actions workflow: `../../.github/workflows/janggi-validation.yml` (repository-root path `.github/workflows/janggi-validation.yml`)

- Trigger: push to `main` and pull requests
- Python: `3.12`
- Compile: `python -m compileall janggi tests tools`
- Test: `python -m unittest discover -s tests -v`

Search benchmark workflow: `../../.github/workflows/janggi-search-benchmark.yml` (repository-root path `.github/workflows/janggi-search-benchmark.yml`)

- Trigger: `workflow_dispatch` and pushes that change `janggi/search.py`, `tools/benchmark_search_ordering.py`, or the workflow itself
- Script: `tools/benchmark_search_ordering.py`
- Purpose: measure deterministic search node counts and legal-move generation work before materially changing search behavior
- Expanded fixture coverage: initial and compact tactical fixtures at their established depths, mixed-material midgame at depth 2, and reduced-material endgame at depths 2 and 3
- A temporary midgame depth-3 experiment exceeded the normal bounded benchmark window, so depth 3 remains a targeted/manual study rather than a regular regression gate

Latest expanded completed benchmark produced these new deterministic baselines:

| Fixture | Depth | Reference nodes | Production nodes | Reduction |
| --- | ---: | ---: | ---: | ---: |
| midgame | 2 | 262 | 108 | 58.78% |
| endgame | 2 | 144 | 72 | 50.00% |
| endgame | 3 | 2053 | 645 | 68.58% |

The completed benchmark preserved the same minimax score across ordering variants and the same production best move for the new fixtures. The temporary midgame depth-3 run is documented as non-production because it did not complete within the bounded review window.

Latest automated validation has also covered the structured coaching action, browser presentation, history-independent checkmate scoring, match undo behavior, and engine-analysis validation.

Render target Blueprint:

- Root Blueprint: `../../render.yaml`
- Service name: `personal-ai-janggi-trainer-by-gpt`
- Desired Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Desired Root Directory: `projects/personal-ai-janggi-trainer-by-gpt`
- Branch: `main`
- Region: Singapore
- Build: `python -m compileall janggi tests`
- Start: `python app.py`
- Desired health check: `/api/health`

Verified live Render state on 2026-09-21:
- Service: `personal-ai-janggi-trainer-by-gpt`
- Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Root Directory: `projects/personal-ai-janggi-trainer-by-gpt`
- Branch: `main`
- Auto Deploy: enabled
- Latest live deployment commit: `f3d2f49dedb6ff1dba70fcc09f5307b04e2822f1`
- Deployment: `dep-dao9rseq1p3s73d3aeq0`
- Deployment status: `live`
- Build: succeeded (`python -m compileall janggi tests`)
- Start: `python app.py`
- URL: `https://personal-ai-janggi-trainer.onrender.com`

The service is now running from the canonical monorepo. Live Render `healthCheckPath` remains empty; application `/api/health` exists and explicit platform health-check configuration is a follow-up operational improvement.

## Explicitly Deferred

- Persistent user accounts and cloud synchronization
- Persistent or cross-instance session storage; current browser sessions live only in one server process and are lost on process restart or replacement
- Database-backed game history
- Trained neural/learned policy or value model
- Production model hosting/model serving
- Full mobile UX and accessibility audit
- Multi-user/social features and monetization
- Production observability, rate limiting, and deployment hardening beyond current Render configuration
- Richer multi-ply tactical motif detection beyond the current bounded double-attack threat

## Architectural Direction

`domain core → match policy → records → engine adapter → search/self-play → training/evaluation → web/API → personal coaching → persistence/authentication/multi-user experience`

The domain model remains authoritative for legality and terminal state. HTTP/browser layers must not duplicate those rules. Engine output must be validated before application. The HTTP layer resolves each browser request to an isolated `TrainerApplication` session before invoking the domain/match layer.

Tactical analysis is intentionally kept at the analysis layer and does not assume a particular engine strength. Immediate tactical risk is one-ply deep. The bounded `double_attack` motif allows one opponent reply and then checks whether the original mover would have legal captures against at least two opposing non-general pieces of at least guard value, while explicitly ignoring the mover's intervening defense. It is therefore a forward-looking warning, not proof of a forced win or loss. Coaching keeps tactical signals separate from score-based severity. Representative fixtures are documented in `docs/TACTICAL_ANALYSIS.md`.

Search remains dependency-free and backend-neutral. Capture-first and checking-move ordering improve alpha-beta effectiveness, the transposition table caches only exact fully searched results keyed by position and remaining depth, the evaluation cache reuses material/mobility scores for repeated positions within one top-level analysis, the check cache avoids recomputing repeated move check status during ordering, and the legal-move cache avoids repeated identical legality generation within one top-level analysis. Terminal checkmate scoring now derives mate distance from search depth rather than historical move count, so search values are consistent with the board-and-turn identity used by the position key. The expanded benchmark now covers initial, tactical, mixed-material midgame, and reduced-material endgame positions. Current production node counts and legal-move generation counts are preserved as deterministic regression baselines. These counts demonstrate reduced duplicated work and fixture-specific alpha-beta behavior, not a universal wall-clock speedup guarantee. The midgame depth-3 study remains outside the mandatory benchmark because it exceeded the normal bounded runtime window.

The non-production check-first ordering experiment matched the current ordering on several fixtures and reduced the compact `double_attack` depth-3 fixture from 896 to 859 nodes. The capture-check-first experiment reduced one capture fixture but regressed the check fixtures and was worse on the double-attack fixture. Production ordering therefore remains capture-value-first followed by checks. Detailed experiment records are kept in `docs/SEARCH_BENCHMARK_HISTORY.md`.

Coaching explanations now add an action-oriented second layer without changing severity rules: recommended captures/checks explain the tactical purpose, acceptable alternatives prompt comparison, inaccuracies prompt one more look for counterplay, and hanging-piece/immediate-capture warnings explicitly focus on the opponent's reply and recapture sequence. The coaching result also exposes a structured `next_action` so presentation layers can show the learner's immediate task without parsing explanatory prose. These changes remain explanatory rather than engine-confidence claims. The current coaching contract and test expectations are documented in `docs/COACHING.md`.

The bounded double-attack detector is explicitly oriented from the original mover's perspective: after one opponent reply, it restores the mover's turn before inspecting potential captures. Regression fixtures cover both a genuine mover-side opportunity and the previously reversed perspective, preventing the heuristic from warning about the opponent's tactical opportunity instead.

Engine analysis now has a single normalization boundary. Best-move recommendations and principal variations are checked against `GameState` before coaching, browser presentation, or the trainer's engine-move response consumes them. A non-empty principal variation must also begin with the normalized best move; inconsistent variations are suppressed. A backend result that is not an `EngineAnalysis` object, or has an invalid analysis perspective, is degraded to an empty analysis for the current side to move; invalid numeric metadata is cleared individually. Malformed analysis is therefore degraded to safe unavailable move data rather than being surfaced as if it were authoritative.

## Known Next Targets

1. Exercise the human-vs-AI turn loop against the live service and close any gameplay/UX defects before increasing engine strength.
2. Upgrade baseline AI strength in measured stages, using the existing deterministic search benchmarks and keeping move legality as the authoritative boundary.
3. Refine bounded tactical analysis only when fixtures reveal a clear coaching gap; avoid silently escalating heuristic signals into strong tactical claims.
4. Use adaptive position-training selection and ephemeral session metrics to evaluate whether repeated coaching signals translate into useful practice interactions, including repeated-problem retry behavior and selection diversity without treating small samples as mastery.
5. Use targeted runtime profiling only when a concrete latency target exists; avoid noisy wall-clock thresholds in mandatory CI.
6. Keep training/evaluation interfaces stable while AI strategy evolves.
