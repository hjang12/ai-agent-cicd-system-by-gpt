# Player Skill Assessment

## Purpose

Player skill assessment is a product-layer contract for measuring a learner independently from the AI model itself.

The current application already has the domain needed to evaluate a completed match. This layer adds the user-side assessment boundary without coupling it to the browser UI, the match engine, or a particular search/ML implementation.

## Two separate evidence streams

### Match rating

A player rating is an Elo-style rating updated from completed games against calibrated opponent models.

Each assessment event stores:

- anonymous player_id;
- game_id;
- player side;
- opponent model_id;
- opponent model_version, when supplied;
- AI level, when supplied;
- opponent rating at game time, when calibrated;
- result from the player's perspective;
- move count;
- rating before/after/delta;
- whether the game was rating-eligible.

The current six AI levels are a search-complexity ladder, not a validated strength ladder. Their ratings are therefore intentionally null. Completed games are still retained as unrated evidence. This avoids producing a numeric player rating from uncalibrated opponents.

### Move-quality profile

Coaching/review data remains separate from rating. A completed game can optionally attach a MoveQualitySummary containing recommended/acceptable/inaccuracy/major-mistake counts and stable coaching reason counts.

Move quality is evidence about decision-making under the current analysis engine. It is not converted directly into Elo.

## Calibration boundary

The intended production flow is:

AI model/version
    ->
self-play and head-to-head evaluation
    ->
calibrated model rating
    ->
player versus model
    ->
PlayerGameAssessment
    ->
PlayerSkillAssessment

When an opponent model has no calibrated rating, the assessment records the result but does not modify the numeric player rating.

The existing model evaluation, tournament, and Elo-style primitives remain responsible for model-versus-model calibration. PlayerSkillAssessment consumes the point-in-time opponent rating rather than deciding model strength itself.

## Historical identity

The rating event stores both model identity and point-in-time opponent rating. A future model version can therefore become stronger while the public AI level stays the same.

A future persistent record should preserve:

game_id
player_id
opponent_model_id
opponent_model_version
opponent_rating_at_game_time
result
rating_before
rating_after
rating_delta

This prevents historical player-rating calculations from silently changing when an AI model is upgraded.

## Provisional status

The player rating status has three states:

- unrated — no games against calibrated opponents yet;
- provisional — at least one rated game, but fewer than the configured established-game threshold;
- established — the configured threshold of rated games has been reached.

The default established-game threshold is a product configuration, not a statistical claim.

## Persistence boundary

The current implementation keeps assessment state in the same isolated in-memory browser session as the match. It is intentionally not durable.

The later persistence layer should store player profile, completed assessment games, rating history, and model metadata independently from GameRecord. Authentication, database choice, and cross-device synchronization remain separate application concerns.

## API

GET /api/assessment returns the current anonymous player's assessment snapshot.

GET /api/state also includes:

- assessment — current player rating/statistics snapshot;
- opponent — the current AI identity/level/calibration metadata.

This keeps the browser contract stable when the UI is redesigned.

## Future skill profile

The future UI can combine, without conflating them:

실전 평가
  rating / provisional status
  wins / draws / losses
  opponent model / level
  rating history

플레이 품질
  recommendation match rate
  mistake distribution
  tactical reason counts
  repeated-mistake evidence

성장
  recent rating change
  recent move-quality trend
  training-problem accuracy

The system should not automatically turn small-sample coaching statistics into a single skill score. A future composite skill model requires separate validation.
