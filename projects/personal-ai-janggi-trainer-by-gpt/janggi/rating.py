from __future__ import annotations

from dataclasses import dataclass

from .training import Outcome


@dataclass(frozen=True)
class RatingUpdate:
    """Result of one Elo update from the first model's perspective."""

    first_rating: int
    second_rating: int
    first_delta: int
    second_delta: int


def expected_score(rating: int, opponent_rating: int) -> float:
    """Return the expected score for a player with the given ratings."""
    _validate_rating(rating)
    _validate_rating(opponent_rating)
    return 1.0 / (1.0 + 10.0 ** ((opponent_rating - rating) / 400.0))


def update_ratings(
    first_rating: int,
    second_rating: int,
    outcome: Outcome,
    *,
    k_factor: int = 32,
) -> RatingUpdate:
    """Apply one Elo update where outcome is from the first model's perspective."""
    _validate_rating(first_rating)
    _validate_rating(second_rating)
    if not isinstance(k_factor, int) or isinstance(k_factor, bool):
        raise ValueError("k_factor must be an integer")
    if k_factor < 1:
        raise ValueError("k_factor must be at least 1")
    if not isinstance(outcome, Outcome):
        raise ValueError("outcome must be an Outcome")

    first_expected = expected_score(first_rating, second_rating)
    first_actual = (outcome.value + 1) / 2.0
    first_delta = round(k_factor * (first_actual - first_expected))
    second_delta = -first_delta
    return RatingUpdate(
        first_rating=first_rating + first_delta,
        second_rating=second_rating + second_delta,
        first_delta=first_delta,
        second_delta=second_delta,
    )


def _validate_rating(rating: int) -> None:
    if not isinstance(rating, int) or isinstance(rating, bool):
        raise ValueError("rating must be an integer")
    if rating < 0:
        raise ValueError("rating must be non-negative")
