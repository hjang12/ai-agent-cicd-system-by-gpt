from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .core import Side
from .rating import RatingUpdate, update_ratings
from .training import Outcome


DEFAULT_PLAYER_RATING = 1000
DEFAULT_K_FACTOR = 32
ESTABLISHED_RATED_GAMES = 20
MAX_GAME_HISTORY = 50
MAX_RATING_HISTORY = 50


@dataclass(frozen=True)
class OpponentProfile:
    """Stable identity/configuration for the model a player faced."""

    model_id: str
    model_version: Optional[str] = None
    ai_level: Optional[str] = None
    rating: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.model_id, str) or not self.model_id.strip():
            raise ValueError("model_id must be a non-empty string")
        if self.model_version is not None and not isinstance(self.model_version, str):
            raise ValueError("model_version must be a string or null")
        if self.ai_level is not None and not isinstance(self.ai_level, str):
            raise ValueError("ai_level must be a string or null")
        if self.rating is not None:
            _validate_rating(self.rating)

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "model_version": self.model_version,
            "ai_level": self.ai_level,
            "rating": self.rating,
        }


@dataclass(frozen=True)
class MoveQualitySummary:
    """Optional per-game coaching summary retained separately from rating."""

    reviewed_moves: int
    recommended: int
    acceptable: int
    inaccuracy: int
    major_mistake: int
    unavailable: int = 0
    reason_counts: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        fields = (
            ("reviewed_moves", self.reviewed_moves),
            ("recommended", self.recommended),
            ("acceptable", self.acceptable),
            ("inaccuracy", self.inaccuracy),
            ("major_mistake", self.major_mistake),
            ("unavailable", self.unavailable),
        )
        for name, value in fields:
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if sum(value for _, value in fields[1:]) != self.reviewed_moves:
            raise ValueError("move-quality counts must sum to reviewed_moves")
        for reason, count in self.reason_counts:
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("reason code must be a non-empty string")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise ValueError("reason count must be a non-negative integer")

    @property
    def recommended_rate(self) -> float:
        return self.recommended / self.reviewed_moves if self.reviewed_moves else 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "reviewed_moves": self.reviewed_moves,
            "recommended": self.recommended,
            "acceptable": self.acceptable,
            "inaccuracy": self.inaccuracy,
            "major_mistake": self.major_mistake,
            "unavailable": self.unavailable,
            "recommended_rate": self.recommended_rate,
            "reason_counts": dict(self.reason_counts),
        }


@dataclass(frozen=True)
class PlayerGameAssessment:
    """One completed player-vs-model assessment event."""

    game_id: str
    player_id: str
    player_side: Side
    opponent: OpponentProfile
    outcome: Outcome
    result_status: str
    move_count: int
    rating_before: int
    rating_after: int
    rating_delta: int
    rating_eligible: bool
    move_quality: Optional[MoveQualitySummary] = None

    def __post_init__(self) -> None:
        if not isinstance(self.game_id, str) or not self.game_id.strip():
            raise ValueError("game_id must be a non-empty string")
        if not isinstance(self.player_id, str) or not self.player_id.strip():
            raise ValueError("player_id must be a non-empty string")
        if not isinstance(self.player_side, Side):
            raise ValueError("player_side must be a Side")
        if not isinstance(self.opponent, OpponentProfile):
            raise ValueError("opponent must be an OpponentProfile")
        if not isinstance(self.outcome, Outcome):
            raise ValueError("outcome must be an Outcome")
        if not isinstance(self.result_status, str) or not self.result_status.strip():
            raise ValueError("result_status must be a non-empty string")
        if not isinstance(self.move_count, int) or isinstance(self.move_count, bool) or self.move_count < 1:
            raise ValueError("move_count must be at least 1")
        _validate_rating(self.rating_before)
        _validate_rating(self.rating_after)
        if not isinstance(self.rating_delta, int) or isinstance(self.rating_delta, bool):
            raise ValueError("rating_delta must be an integer")
        if self.rating_after - self.rating_before != self.rating_delta:
            raise ValueError("rating delta must match before/after ratings")
        if not isinstance(self.rating_eligible, bool):
            raise ValueError("rating_eligible must be boolean")
        if self.rating_eligible and self.opponent.rating is None:
            raise ValueError("rated games require an opponent rating")
        if self.move_quality is not None and not isinstance(self.move_quality, MoveQualitySummary):
            raise ValueError("move_quality must be a MoveQualitySummary or null")

    def to_dict(self) -> dict[str, object]:
        return {
            "game_id": self.game_id,
            "player_id": self.player_id,
            "player_side": self.player_side.value,
            "opponent": {
                "model_id": self.opponent.model_id,
                "model_version": self.opponent.model_version,
                "ai_level": self.opponent.ai_level,
                "rating": self.opponent.rating,
            },
            "outcome": self.outcome.value,
            "result_status": self.result_status,
            "move_count": self.move_count,
            "rating_before": self.rating_before,
            "rating_after": self.rating_after,
            "rating_delta": self.rating_delta,
            "rating_eligible": self.rating_eligible,
            "move_quality": self.move_quality.to_dict() if self.move_quality else None,
        }


class PlayerSkillAssessment:
    """Aggregate anonymous-player skill evidence for one browser session.

    Rating updates are deliberately disabled until the opponent model has a
    calibrated rating. Completed game outcomes are retained as unrated evidence
    so a later persistence/calibration layer can replay them without changing
    the public assessment contract.
    """

    def __init__(
        self,
        player_id: str,
        *,
        initial_rating: int = DEFAULT_PLAYER_RATING,
        k_factor: int = DEFAULT_K_FACTOR,
        established_rated_games: int = ESTABLISHED_RATED_GAMES,
    ) -> None:
        if not isinstance(player_id, str) or not player_id.strip():
            raise ValueError("player_id must be a non-empty string")
        _validate_rating(initial_rating)
        if not isinstance(k_factor, int) or isinstance(k_factor, bool) or k_factor < 1:
            raise ValueError("k_factor must be a positive integer")
        if (
            not isinstance(established_rated_games, int)
            or isinstance(established_rated_games, bool)
            or established_rated_games < 1
        ):
            raise ValueError("established_rated_games must be at least 1")

        self.player_id = player_id
        self.initial_rating = initial_rating
        self.k_factor = k_factor
        self.established_rated_games = established_rated_games
        self._rating = initial_rating
        self._games = 0
        self._wins = 0
        self._draws = 0
        self._losses = 0
        self._rated_games = 0
        self._unrated_games = 0
        self._games_history: list[PlayerGameAssessment] = []
        self._rating_history: list[int] = [initial_rating]

    def record_game(
        self,
        *,
        game_id: str,
        player_side: Side,
        opponent: OpponentProfile,
        outcome: Outcome,
        result_status: str,
        move_count: int,
        move_quality: Optional[MoveQualitySummary] = None,
    ) -> PlayerGameAssessment:
        if any(game.game_id == game_id for game in self._games_history):
            raise ValueError(f"game id already recorded: {game_id}")

        rating_before = self._rating
        rating_eligible = opponent.rating is not None
        rating_delta = 0
        rating_after = rating_before

        if rating_eligible:
            rating_update: RatingUpdate = update_ratings(
                rating_before,
                opponent.rating,
                outcome,
                k_factor=self.k_factor,
            )
            rating_after = rating_update.first_rating
            rating_delta = rating_update.first_delta
            self._rated_games += 1
            self._rating = rating_after
            self._rating_history.append(rating_after)
            if len(self._rating_history) > MAX_RATING_HISTORY:
                del self._rating_history[:-MAX_RATING_HISTORY]
        else:
            self._unrated_games += 1

        self._games += 1
        if outcome is Outcome.WIN:
            self._wins += 1
        elif outcome is Outcome.DRAW:
            self._draws += 1
        else:
            self._losses += 1

        game = PlayerGameAssessment(
            game_id=game_id,
            player_id=self.player_id,
            player_side=player_side,
            opponent=opponent,
            outcome=outcome,
            result_status=result_status,
            move_count=move_count,
            rating_before=rating_before,
            rating_after=rating_after,
            rating_delta=rating_delta,
            rating_eligible=rating_eligible,
            move_quality=move_quality,
        )
        self._games_history.append(game)
        if len(self._games_history) > MAX_GAME_HISTORY:
            del self._games_history[:-MAX_GAME_HISTORY]
        return game

    @property
    def games(self) -> int:
        return self._games

    @property
    def wins(self) -> int:
        return self._wins

    @property
    def draws(self) -> int:
        return self._draws

    @property
    def losses(self) -> int:
        return self._losses

    @property
    def rated_games(self) -> int:
        return self._rated_games

    @property
    def unrated_games(self) -> int:
        return self._unrated_games

    @property
    def rating(self) -> int:
        return self._rating

    @property
    def rating_status(self) -> str:
        if self._rated_games == 0:
            return "unrated"
        if self._rated_games < self.established_rated_games:
            return "provisional"
        return "established"

    @property
    def rating_available(self) -> bool:
        return self._rated_games > 0

    def snapshot(self) -> dict[str, object]:
        last_game = self._games_history[-1] if self._games_history else None
        return {
            "player_id": self.player_id,
            "rating": self._rating if self.rating_available else None,
            "rating_status": self.rating_status,
            "games": self._games,
            "wins": self._wins,
            "draws": self._draws,
            "losses": self._losses,
            "rated_games": self._rated_games,
            "unrated_games": self._unrated_games,
            "win_rate": self._wins / self._games if self._games else 0.0,
            "rating_history": list(self._rating_history) if self.rating_available else [],
            "last_game": last_game.to_dict() if last_game else None,
        }


def outcome_from_result(player_side: Side, result_status: str) -> Outcome:
    """Map a terminal match status to the player's perspective."""
    if not isinstance(player_side, Side):
        raise ValueError("player_side must be a Side")
    if not isinstance(result_status, str):
        raise ValueError("result_status must be a string")

    if result_status in {
        "draw_bikjang",
        "draw_repetition",
        "draw_consecutive_pass",
        "draw_stalemate",
    }:
        return Outcome.DRAW
    if result_status == "cho_win":
        return Outcome.WIN if player_side is Side.CHO else Outcome.LOSS
    if result_status == "han_win":
        return Outcome.WIN if player_side is Side.HAN else Outcome.LOSS
    raise ValueError("result_status must be a terminal match status")


def _validate_rating(rating: int) -> None:
    if not isinstance(rating, int) or isinstance(rating, bool):
        raise ValueError("rating must be an integer")
    if rating < 0:
        raise ValueError("rating must be non-negative")
