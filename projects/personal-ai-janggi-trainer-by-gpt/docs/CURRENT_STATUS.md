# Current Status

## Governance

- Common Governance Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Governance Version: `1.3.3`
- Governance status: active baseline on `main`
- Project context entrypoint: `AGENT_START.md`

## Product

- Project: Personal AI Janggi Trainer
- Canonical Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Project Path: `projects/personal-ai-janggi-trainer-by-gpt/`
- Default branch: `main`
- Primary user: one self-directed Janggi learner using a desktop browser
- Current priority: resume provenance-aware adjacent AI-level calibration (`2-3 → 3-4 → 4-5 → 5-6`) while preserving the engine/evaluation boundaries; actual off-CI execution is currently blocked in this runtime.

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
- Player skill-assessment foundation that records completed player-vs-AI outcomes, opponent model/version identity, point-in-time opponent ratings when calibrated, and unrated evidence while calibration is pending
- Dependency-free browser trainer and HTTP API
- Per-browser in-memory session isolation using an opaque HttpOnly SameSite cookie, so separate browser sessions no longer share the same `Match` or training state
- Browser analysis panel shows tactical risk, bounded tactical warnings, recommendation principal variation, and structured next-action coaching; principal variations use learner-facing board notation (`a1`–`i10`) with numbered plies and side labels, terminal results are localized, and turn handoff is explicit in the heading
- Browser engine-move result also shows the engine principal variation, normalized evaluation score, search depth, and visited-node count as learning aids
- Browser UI redesigned around a board-first, mobile-friendly game screen with explicit new-game settings, side/opponent cards, player assessment summary, and compact action controls
- Browser board selection now has an explicit selected-piece marker and legal-destination highlight, and the board shows a persistent AI-thinking overlay during the `/api/engine/move` request.
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
- `GET /api/assessment` — read the current anonymous player's skill-assessment snapshot
- Move analysis API includes `tactical_risk` (`none`, `immediate_capture`, `hanging_piece`) and `tactical_motifs` (currently `double_attack` when detected)
- Move coaching API includes `severity`, `message`, `score_delta_cp`, presentation-ready `next_action`, and stable `reason_codes` for future repeated-mistake aggregation
- Engine move analysis includes principal variation data after authoritative legality normalization
- Position-training problems preserve the original pre-move state, hide the target move by default, and reuse the existing coaching reason/severity contract
- Training metrics reset with the match and are never promoted to persistent user or model-training data; problem-level repeated-mistake counts and reason-specific accuracy are derived from the same ephemeral counts, and adaptive selection uses those counts only for the current session

## Current UI Direction

- The trainer is a scroll-free, single-screen game application with the Janggi board as the dominant surface.
- During a normal game, only player/turn context, the compact game status, and the essential actions remain visible around the board.
- Settings, analysis, review, training, and player assessment are not persistent side content; they are opened explicitly from the header.
- Desktop drawers use dedicated layout columns, so opening a drawer reduces the game-stage width instead of covering the board.
- Mobile drawers use a second layout row below the game stage, so opening them consumes viewport space instead of covering the board.
- The post-game result surface is part of normal layout flow rather than an absolute board overlay.
- UX-001 and UX-002 remain protected, and UX-003 now also has the non-overlap UX-004 companion contract.
- This UI remains independent from Engine/search implementation so AI-strength calibration can resume on the same stable product shell.

## Latest Verification (2026-10-01)

- UI redesign merged to `main` as PR #89, merge commit `2886a0d940f951929edc6d53f501e1133018cc44`.
- The last verified code-bearing Janggi validation passed compile, Requirement Contract validation, and the full unit-test suite; exact run/commit identifiers are preserved in dated verification/history records.
- The last verified Workspace validation passed; exact run/commit identifiers are preserved in dated verification/history records.
- The PR initially exposed one stale browser regression assertion for the removed v2 board-width rule; that assertion was updated and the rerun passed. No product logic failure was identified.
- Static main verification confirms UX-004 layout rules are present and the former fixed-drawer / full-screen overlay CSS is absent.
- Render workspace access is restored. The current Render service is confirmed `live` on main commit `6235be60004e06084f551d87e44907cc07a72a30` via deployment `dep-dav07ue0tbcc73e81kf0`; build/start completed normally.
- External browser/UI smoke verification is still unavailable from this agent runtime because the available web verifier rejects the public Render URL and the runtime cannot resolve the public hostname. This is a verification-environment limitation, not a confirmed product or Render outage.

## Active Execution Constraints

- The authoritative workspace issue index is `../../../GOVERNANCE/docs/ACTIVE_ISSUES.md`.
- Off-CI provenance-aware calibration for 2-3 through 5-6 still requires an execution environment capable of running the private repository outside the fast CI path.
- Live Render deployment state is verified through Render tooling, but direct browser/UI smoke verification remains unavailable from this agent runtime.

## Development Safety

- Requirement Contract Registry: `docs/requirement_contracts.json`
- Human-readable contract context: `docs/REQUIREMENT_CONTRACTS.md`
- Current protected product invariant: `UX-001` — human move must be visibly rendered before AI calculation begins
- Current protected gameplay feedback invariant: `UX-002` — selected piece / legal destinations are visibly marked and AI thinking is explicitly shown on-board until response completion or recovery
- Contract validation: `tools/validate_requirement_contracts.py` runs in the mandatory Janggi validation workflow
- Contract rule: existing `ACTIVE` user requirements are preserved across later implementation/refactoring work; intentional behavior changes require explicit declaration and user-facing report before superseding the Contract

## CI/CD

GitHub Actions workflow: `../../.github/workflows/janggi-validation.yml` (repository-root path `.github/workflows/janggi-validation.yml`)

- Trigger: push to `main` and pull requests
- Python: `3.12`
- Compile: `python -m compileall janggi tests tools`
- Test: `python -m unittest discover -s tests -v`
- Workspace validation runs `tools/validate_workspace.py`; no separate context-consistency parser is part of the current Governance validation path.

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

Verified live Render state on 2026-10-01:
- Service: `personal-ai-janggi-trainer-by-gpt`
- Repository: `hjang12/ai-agent-cicd-system-by-gpt`
- Root Directory: `projects/personal-ai-janggi-trainer-by-gpt`
- Branch: `main`
- Auto Deploy: enabled
- Last independent live verification: 2026-10-01; exact deployment identity is preserved in dated verification/history records.
- Build: succeeded (`python -m compileall janggi tests`)
- Start: `python app.py`
- URL: `https://personal-ai-janggi-trainer.onrender.com`

Later main commits through the documentation review are documentation-only but are inside the Janggi service build filter, so Render can legitimately redeploy them. They do not change application code or the application runtime behavior. The Render Blueprint declares `/api/health`. The connected Render service metadata currently does not expose a mutable health-check field through the available toolset; this is tracked as the existing workspace platform hardening item, not as a user action or application outage.

## Explicitly Deferred

- Persistent user accounts and cloud synchronization
- Persistent player rating/history storage and cross-device skill profiles
- Persistent or cross-instance session storage; current browser sessions live only in one server process and are lost on process restart or replacement
- Database-backed game history
- Trained neural/learned policy or value model (production promotion remains deferred; the ValueModel interface, self-play dataset generator, and dependency-free linear candidate trainer are now in place)
- Production model hosting/model serving
- Full mobile UX and accessibility audit
- Multi-user/social features and monetization
- Production observability, rate limiting, and deployment hardening beyond current Render configuration
- Richer multi-ply tactical motif detection beyond the current bounded double-attack threat

## Architectural Direction

`domain core → match policy → records → engine adapter → search/self-play → training/evaluation → web/API → personal coaching → persistence/authentication/multi-user experience`

The domain model remains authoritative for legality and terminal state. HTTP/browser layers must not duplicate those rules. Engine output must be validated before application. The HTTP layer resolves each browser request to an isolated `TrainerApplication` session before invoking the domain/match layer.

Tactical analysis is intentionally kept at the analysis layer and does not assume a particular engine strength. Immediate tactical risk is one-ply deep. The bounded `double_attack` motif allows one opponent reply and then checks whether the original mover would have legal captures against at least two opposing non-general pieces of at least guard value, while explicitly ignoring the mover's intervening defense. It is therefore a forward-looking warning, not proof of a forced win or loss. Coaching keeps tactical signals separate from score-based severity. Representative fixtures are documented in `docs/TACTICAL_ANALYSIS.md`.

A reproducible self-play dataset path is now available through `tools/generate_self_play_dataset.py` and the manual `janggi-self-play-dataset.yml` workflow. A dependency-free `LinearValueModel`/`LinearValueTrainer` is now available for candidate-model experiments; it is not connected to the public AI levels or production evaluator.
 A reproducible candidate-strength harness also compares that model against the current heuristic under the same search-level budget; the result remains evidence-only until repeated completed-game tests justify promotion.
 It reuses the authoritative self-play/record-validation/training-data pipeline and keeps incomplete games out of value labels.

The search engine now also has an optional ValueModel boundary. A model receives a history-free GameState and returns an integer centipawn-like value while the search retains ownership of terminal mate scoring. The default heuristic path remains unchanged, so learned-value experiments can be isolated from the browser, match, coaching, and public AI-level layers.

Search remains dependency-free and backend-neutral. Capture-first and checking-move ordering improve alpha-beta effectiveness, the transposition table stores exact/lower/upper bounds keyed by position, remaining depth, and noisy-state semantics and reuses lower/upper bounds only when their cutoff conditions are satisfied, the evaluation cache reuses material/mobility scores for repeated positions within one top-level analysis, the check cache avoids recomputing repeated move check status during ordering, and the legal-move cache avoids repeated identical legality generation within one top-level analysis. Terminal checkmate scoring now derives mate distance from search depth rather than historical move count, so search values are consistent with the board-and-turn identity used by the position key. The expanded benchmark now covers initial, tactical, mixed-material midgame, and reduced-material endgame positions. Current production node counts and legal-move generation counts are preserved as deterministic regression baselines. These counts demonstrate reduced duplicated work and fixture-specific alpha-beta behavior, not a universal wall-clock speedup guarantee. The midgame depth-3 study remains outside the mandatory benchmark because it exceeded the normal bounded runtime window.

The non-production check-first ordering experiment matched the current ordering on several fixtures and reduced the compact `double_attack` depth-3 fixture from 896 to 859 nodes. The capture-check-first experiment reduced one capture fixture but regressed the check fixtures and was worse on the double-attack fixture. Production ordering therefore remains capture-value-first followed by checks. Detailed experiment records are kept in `docs/SEARCH_BENCHMARK_HISTORY.md`.

Coaching explanations now add an action-oriented second layer without changing severity rules: recommended captures/checks explain the tactical purpose, acceptable alternatives prompt comparison, inaccuracies prompt one more look for counterplay, and hanging-piece/immediate-capture warnings explicitly focus on the opponent's reply and recapture sequence. The coaching result also exposes a structured `next_action` so presentation layers can show the learner's immediate task without parsing explanatory prose. These changes remain explanatory rather than engine-confidence claims. The current coaching contract and test expectations are documented in `docs/COACHING.md`.

The bounded double-attack detector is explicitly oriented from the original mover's perspective: after one opponent reply, it restores the mover's turn before inspecting potential captures. Regression fixtures cover both a genuine mover-side opportunity and the previously reversed perspective, preventing the heuristic from warning about the opponent's tactical opportunity instead.

Engine analysis now has a single normalization boundary. Best-move recommendations and principal variations are checked against `GameState` before coaching, browser presentation, or the trainer's engine-move response consumes them. A non-empty principal variation must also begin with the normalized best move; inconsistent variations are suppressed. A backend result that is not an `EngineAnalysis` object, or has an invalid analysis perspective, is degraded to an empty analysis for the current side to move; invalid numeric metadata is cleared individually. Malformed analysis is therefore degraded to safe unavailable move data rather than being surfaced as if it were authoritative.

## Current Calibration Execution State

- Long-running AI level calibration is intentionally separated from GitHub Actions.
- Off-CI calibration infrastructure from PR #84 is merged; no calibration implementation PR is currently open.
- PR #84 merged after Workspace and Janggi validation passed; fast project CI is operational again, while long-running calibration remains intentionally off-CI.
- The off-CI runner now validates existing artifact identity and avoids cross-setup aggregation.
- A legacy single-seed 2-3 artifact exists (10/10 completed, higher level 10-0), but it is not sufficient under the current provenance-aware two-seed evidence boundary. Actual sufficient 2-3 / 3-4 / 4-5 / 5-6 calibration computation remains incomplete; no strength result is inferred from infrastructure readiness or one-seed legacy evidence.

## Actual level-strength calibration evidence

- PR smoke calibration pipeline remains operational for bounded validation only.
- Smoke configuration remains: 2 games per adjacent pair, 4 plies per game; its 0/10 completed result is not playing-strength evidence.
- The calibration request runner now supports repository-root request files through `GITHUB_WORKSPACE`; PR #76 added the request path and PR #78 corrected the working-directory path resolution.
- First 1-2 evidence run at 48 plies was insufficient (1/10 completed, 9 unfinished), so the evidence run was raised to 96 plies.
- 1-2 seed 20260930 at 96 plies: 9/10 completed, 1 unfinished, score 4.0 vs 5.0.
- 1-2 seed 20261001 at 96 plies: 12/12 completed, score 5.5 vs 6.5.
- 1-2 aggregate: 21/22 completed, 1 unfinished, 4.545% unfinished, 2 seeds; the evidence thresholds are satisfied and the higher-numbered level scored higher descriptively (11.5 vs 9.5).
- These results do not authorize public level promotion, search-budget changes, or a six-level ordering conclusion. Adjacent pairs 2-3 through 5-6 remain uncalibrated.
- Calibration artifacts retain per-game terminal status/outcome/ply evidence, and `tools/evaluate_ai_level_evidence.py` remains the review gate. Default review thresholds are 20 completed games/pair, <=25% unfinished, and at least 2 seeds.

## Known Next Targets

1. Verify the game-first UI and human-vs-AI turn loop against the live service, then close any remaining gameplay/UX defects.
2. Resume calibration for adjacent pairs 2-3, 3-4, 4-5, and 5-6 with sufficient seeded completed-game evidence before changing public AI level search budgets.
3. Upgrade baseline AI strength in measured stages, using the existing deterministic search benchmarks and keeping move legality as the authoritative boundary.
4. Refine bounded tactical analysis only when fixtures reveal a clear coaching gap; avoid silently escalating heuristic signals into strong tactical claims.
5. Use player skill-assessment evidence together with adaptive position-training selection and ephemeral session metrics, while keeping match rating separate from coaching statistics and preventing uncalibrated AI levels from producing numeric player ratings.
6. Use targeted runtime profiling only when a concrete latency target exists; avoid noisy wall-clock thresholds in mandatory CI.
7. Keep training/evaluation interfaces stable while AI strategy evolves.
