# Model Evaluation

Model comparison is kept separate from the search implementation.

`HeadToHeadEvaluator` runs one model-vs-model game through `Match`, so move legality and terminal rules remain authoritative in the domain layer. A completed game can optionally produce a `RatingUpdate` using the Elo utilities.

`HeadToHeadTournament` repeats that evaluation and can alternate colors between games. `EvaluationSummary` reports wins, draws, losses, and match points for the two named models.

Games capped by `max_plies` remain `PLAYING` and are intentionally not rating-eligible. This avoids converting an interrupted self-play run into a false win or draw.

The current layer does not persist ratings or define a leaderboard. Those concerns belong to a later application/storage layer.
