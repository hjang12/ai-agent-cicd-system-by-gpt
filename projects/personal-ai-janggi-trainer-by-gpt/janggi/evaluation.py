from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .core import Move, Side
from .engine import Engine, validate_engine_move
from .match import GameStatus, Match, RuleSet
from .rating import RatingUpdate, update_ratings
from .training import Outcome


@dataclass(frozen=True)
class EvaluationGame:
    """One completed or capped head-to-head model game."""

    first_model_id: str
    second_model_id: str
    moves: tuple[Move, ...]
    status: GameStatus
    rating_update: Optional[RatingUpdate] = None

    @property
    def outcome_for_first(self) -> Outcome:
        return _outcome_for_first(self.status)


class HeadToHeadEvaluator:
    """Run model-vs-model games using the authoritative match rules."""

    def __init__(
        self,
        first_engine: Engine,
        second_engine: Engine,
        *,
        first_model_id: str,
        second_model_id: str,
        rules: Optional[RuleSet] = None,
        max_plies: int = 512,
    ) -> None:
        if not first_model_id.strip() or not second_model_id.strip():
            raise ValueError("model ids must not be empty")
        if first_model_id == second_model_id:
            raise ValueError("model ids must be distinct")
        if max_plies < 1:
            raise ValueError("max_plies must be at least 1")
        self.first_engine = first_engine
        self.second_engine = second_engine
        self.first_model_id = first_model_id
        self.second_model_id = second_model_id
        self.rules = rules or RuleSet()
        self.max_plies = max_plies

    def play_game(
        self,
        *,
        first_rating: Optional[int] = None,
        second_rating: Optional[int] = None,
        k_factor: int = 32,
        setup: str = "classic",
    ) -> EvaluationGame:
        match = Match.new(setup=setup, rules=self.rules)
        moves: list[Move] = []

        for _ in range(self.max_plies):
            if match.status is not GameStatus.PLAYING:
                break
            engine = self.first_engine if match.state.turn is Side.CHO else self.second_engine
            proposed_move = engine.choose_move(match.state)
            move = validate_engine_move(engine, match.state, proposed_move)
            moves.append(move)
            match = match.play(move)

        status = match.status
        rating_update = None
        if status is not GameStatus.PLAYING and first_rating is not None and second_rating is not None:
            rating_update = update_ratings(
                first_rating,
                second_rating,
                _outcome_for_first(status),
                k_factor=k_factor,
            )
        return EvaluationGame(
            first_model_id=self.first_model_id,
            second_model_id=self.second_model_id,
            moves=tuple(moves),
            status=status,
            rating_update=rating_update,
        )


def _outcome_for_first(status: GameStatus) -> Outcome:
    if status is GameStatus.CHO_WIN:
        return Outcome.WIN
    if status is GameStatus.HAN_WIN:
        return Outcome.LOSS
    if status in {
        GameStatus.DRAW_BIKJANG,
        GameStatus.DRAW_REPETITION,
        GameStatus.DRAW_CONSECUTIVE_PASS,
        GameStatus.DRAW_STALEMATE,
    }:
        return Outcome.DRAW
    raise ValueError("status must be terminal")
