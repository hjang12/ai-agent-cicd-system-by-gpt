from __future__ import annotations

from typing import Protocol

from .core import GameState


VALUE_MODEL_SCORE_LIMIT = 100_000


class ValueModel(Protocol):
    """Backend-neutral value model consumed by NegamaxEngine.

    The model predicts a centipawn-like integer from the side-to-move perspective.
    The search layer removes move history before calling the model so the model
    follows the same board-and-turn identity used by the evaluation cache.
    """

    def predict_cp(self, state: GameState) -> int:
        """Return the position value from state.turn's perspective."""
        ...


def validate_value_score(score: int) -> int:
    """Validate a model score while reserving the search mate-score range."""
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("value model score must be an integer")
    if not -VALUE_MODEL_SCORE_LIMIT < score < VALUE_MODEL_SCORE_LIMIT:
        raise ValueError("value model score must stay below the reserved mate-score range")
    return score
