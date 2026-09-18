# Personal AI Janggi Trainer

A personal training environment for learning, reviewing, and improving at Korean chess (Janggi).

## Current stage

The project has a dependency-free Janggi domain and match layer with board state, standard initial setup variants, piece movement, move legality, check/bikjang detection, pass handling, position keys, move history, game records, JSON serialization, replay, match status, and configurable match-policy rules. Match state can be restored by undoing the most recent move without reproducing history logic in the browser.

The engine boundary is defined separately from the domain model. The move-analysis layer normalizes an engine's position analysis into a stable result for coaching and future training pipelines. Engine recommendations and principal variations are checked against the authoritative domain state before they reach coaching or browser presentation, so malformed move data is suppressed rather than treated as valid guidance. A conservative coaching layer translates that raw analysis into learner-facing severity and explanation without changing the engine or rules model. The human-record pipeline separates structural/replay validity from game completeness and training-data eligibility. A dependency-free negamax search backend provides the first real move-search implementation for self-play and integration testing, including optional seedable root-level tie randomization for self-play diversity. The training layer converts accepted completed records into position/action/value samples and rejects samples whose actions are not legal from their stored pre-move states. Model metadata and head-to-head evaluation/rating primitives are also available.

## Browser trainer

`index.html` is connected to the small dependency-free HTTP boundary in `app.py`. The browser can load the authoritative state, select a piece and legal destination, preview the selected move against the baseline engine, show conservative coaching feedback, reset among supported setup variants, undo the latest move, and request a baseline engine move.

The browser analysis panel exposes the coaching result together with the move, recommendation, score delta, tactical-risk signal, bounded tactical motif warning, and principal variation. The UI presentation consumes backend analysis data rather than reimplementing Janggi rules or search logic.

The server exposes:

- `GET /` — browser trainer shell
- `GET /api/health` — service health
- `GET /api/state` — current match snapshot and legal moves
- `GET /api/record` — current session record
- `POST /api/reset` — reset session/setup
- `POST /api/move` — apply a player move through `Match`
- `POST /api/undo` — restore the match state immediately before the latest move
- `POST /api/analyze/move` — analyze a legal move and return coaching insight without changing the active match
- `POST /api/engine/move` — analyze, validate, and apply a baseline engine move (browser exposes this as the opponent/Han turn)

See `docs/API.md` for the transport contract, `docs/ARCHITECTURE.md` for module boundaries, and `docs/COACHING.md` for the learner-feedback contract.

## Repository map

- `index.html` — dependency-free browser trainer shell
- `app.py` — dependency-free HTTP application boundary
- `../../render.yaml` — monorepo root Render service configuration
- `janggi/core.py` — authoritative board and move-legality domain model
- `janggi/match.py` — match lifecycle and configurable game-end policy
- `janggi/record.py` — game/state serialization and replay
- `janggi/engine.py` — backend-neutral engine protocol and validation helpers
- `janggi/analysis.py` — backend-neutral move/position analysis results
- `janggi/coaching.py` — conservative learner-facing move quality classification and explanations
- `janggi/pipeline.py` — record validation and training-candidate classification
- `janggi/search.py` — dependency-free negamax/alpha-beta search backend
- `janggi/self_play.py` — engine-vs-engine game generation and pipeline validation
- `janggi/training.py` — position/action/value training examples and dataset builder
- `janggi/model.py` — stable model metadata registry
- `janggi/evaluation.py` — model-vs-model evaluation primitives
- `janggi/tournament.py` — repeated head-to-head evaluation aggregation
- `janggi/rating.py` — Elo-style rating calculations
- `tests/` — unit and application-boundary tests
- `tools/benchmark_search_ordering.py` — deterministic search-ordering and legal-move-generation benchmark
- `docs/PRODUCT_BRIEF.md` — product scope and MVP criteria
- `docs/ARCHITECTURE.md` — module boundaries and future extension points
- `docs/API.md` — web/API transport contract
- `docs/JANGGI_RULES.md` — rules and coordinate contract used by the core
- `docs/ENGINE_API.md` — engine adapter contract
- `docs/SELF_PLAY.md` — self-play generation contract
- `docs/TRAINING_DATA.md` — position/action/value dataset contract
- `docs/COACHING.md` — coaching severity and explanation contract
- `docs/SEARCH.md` — current search architecture and benchmark interpretation
- `docs/SEARCH_BENCHMARK_HISTORY.md` — persistent search benchmark decision history
- `../../.github/workflows/janggi-validation.yml` — Python 3.12 compile/test validation
- `../../.github/workflows/janggi-search-benchmark.yml` — deterministic search benchmark

## Monorepo operation

This project is developed inside the canonical workspace repository `hjang12/ai-agent-cicd-system-by-gpt` under `projects/personal-ai-janggi-trainer-by-gpt/`. The project-local source, tests, and Context remain isolated from sibling projects. Shared CI and Render configuration live at the workspace root.

## Working principles

1. GitHub is the source of truth; changes are made and reviewed here.
2. No external open-source dependency is added until its license is reviewed.
3. No version numbers are invented or advanced without discussion.
4. AI, storage, and framework choices stay open until requirements are validated.
5. User games are personal analysis/coaching data, not unquestioned ground-truth labels for the core AI.
6. HTTP and browser layers must not duplicate Janggi legality or terminal-state rules.
7. Engine analysis is treated as untrusted backend output and normalized against `GameState` before it is surfaced to higher layers.

## Development direction

`domain core → match policy → records → engine adapter → search/self-play → training/evaluation → web/API → personal coaching → persistence/authentication/multi-user experience`

The current web layer is deliberately small. It establishes the deployment/API boundary without committing the project to a third-party Python framework, database, authentication provider, or trained model. Stronger search, learned evaluation, persistence, authentication, and production session management can be added behind the existing boundaries.
