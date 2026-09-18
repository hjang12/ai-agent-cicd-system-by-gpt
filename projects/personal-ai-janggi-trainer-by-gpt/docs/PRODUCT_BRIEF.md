# MVP Product Brief

## Problem

Solo Janggi learners need a focused place to turn practice into a repeatable coaching habit. Generic board sites do not yet provide a personal, explainable training loop tailored to Janggi.

## Primary user

One self-directed player using a desktop browser. Multi-user play, social features, accounts, and monetization remain outside the first MVP.

## Current backend and application foundation

The project now has a dependency-free Janggi rules engine, match/result handling, game-record validation, engine abstraction, depth-limited search, self-play generation, training-dataset construction, model metadata, head-to-head evaluation/rating infrastructure, and a small dependency-free HTTP application layer.

The browser prototype now consumes the application API for authoritative state, legal moves, move coaching, session reset, one-ply undo, and baseline-engine moves. Persistent storage and production authentication are still deferred.

## First useful product loop

1. Open the trainer.
2. Start a local practice session.
3. See a board and a clear coaching status.
4. Choose a legal move.
5. Review that move against the baseline engine recommendation.
6. Continue with the engine as an opponent or undo a recent move to retry a position.
7. Preserve evaluated positions as training data for future model improvement.

## In scope now

- Static, dependency-free browser shell
- 9×10 Janggi board representation
- Local practice-session UI
- Dependency-free HTTP application layer
- JSON API for health, state, reset, moves, undo, move analysis, and engine moves
- Authoritative Janggi move legality and match rules in Python
- Human game-record validation and training-data pipeline
- Dependency-free search baseline
- Self-play and batch game generation
- Model metadata registry and head-to-head evaluation/rating primitives
- Product and technical decision records

## Explicitly deferred

- Persistent user accounts and cloud synchronization
- Database-backed game history
- Trained neural or learned policy/value model
- Production model hosting and model-serving infrastructure
- Full mobile UX and accessibility audit
- Multi-user play, social features, and monetization
- Production observability, rate limiting, and deployment hardening beyond the current Render configuration

## MVP success criteria

- A prospective user can understand the intended coaching loop in under a minute.
- The board interaction remains usable in a modern desktop browser.
- The Python domain model is authoritative for legal move and match-state decisions.
- No external code or data dependency is required for the baseline backend.
- Engine output is validated against the domain model before being applied.
- A played move can be analyzed without mutating the active game state.
- A recent move can be undone without reproducing match-state logic in the browser.
- Training data is generated only from records that pass the defined validation pipeline.
- The next persistence/model/deployment decision has a documented evaluation path.