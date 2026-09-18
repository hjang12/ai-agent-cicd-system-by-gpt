# Model Ratings

The project uses a small dependency-free Elo utility to compare model strength through repeated head-to-head games.

`expected_score(rating, opponent_rating)` returns the standard Elo expected score in the range 0 to 1.

`update_ratings(first_rating, second_rating, outcome, k_factor=32)` applies one result from the first model's perspective. `Outcome.WIN`, `Outcome.DRAW`, and `Outcome.LOSS` map to actual scores of 1, 0.5, and 0. The two rating changes are equal and opposite.

These helpers do not define a production leaderboard policy. They provide the arithmetic layer needed by future model-evaluation jobs. Initial model ratings should remain explicit metadata rather than being inferred automatically from the search depth or engine name.
