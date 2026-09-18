from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .engine import Engine
from .evaluation import EvaluationGame, HeadToHeadEvaluator
from .match import GameStatus, RuleSet


@dataclass(frozen=True)
class EvaluationSummary:
    """Aggregate results for repeated head-to-head games."""

    first_model_id: str
    second_model_id: str
    games: tuple[EvaluationGame, ...]

    @property
    def first_wins(self) -> int:
        return sum(
            game.outcome_for_first.value == 1
            for game in self.games
            if game.status is not GameStatus.PLAYING
        )

    @property
    def second_wins(self) -> int:
        return sum(
            game.outcome_for_first.value == -1
            for game in self.games
            if game.status is not GameStatus.PLAYING
        )

    @property
    def draws(self) -> int:
        return sum(
            game.outcome_for_first.value == 0
            for game in self.games
            if game.status is not GameStatus.PLAYING
        )

    @property
    def unfinished(self) -> int:
        return sum(game.status is GameStatus.PLAYING for game in self.games)

    @property
    def completed(self) -> int:
        return len(self.games) - self.unfinished

    @property
    def first_score(self) -> float:
        return self.first_wins + self.draws * 0.5

    @property
    def second_score(self) -> float:
        return self.second_wins + self.draws * 0.5


class HeadToHeadTournament:
    """Run repeated head-to-head games with optional color alternation."""

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
        self.first_engine = first_engine
        self.second_engine = second_engine
        self.first_model_id = first_model_id
        self.second_model_id = second_model_id
        self.rules = rules or RuleSet()
        self.max_plies = max_plies

    def run(
        self,
        games: int,
        *,
        alternate_colors: bool = True,
        setup: str = "classic",
    ) -> EvaluationSummary:
        if games < 1:
            raise ValueError("games must be at least 1")

        results: list[EvaluationGame] = []
        for index in range(games):
            if alternate_colors and index % 2 == 1:
                swapped = HeadToHeadEvaluator(
                    self.second_engine,
                    self.first_engine,
                    first_model_id=self.second_model_id,
                    second_model_id=self.first_model_id,
                    rules=self.rules,
                    max_plies=self.max_plies,
                ).play_game(setup=setup)
                game = EvaluationGame(
                    first_model_id=self.first_model_id,
                    second_model_id=self.second_model_id,
                    moves=swapped.moves,
                    status=_swap_status(swapped.status),
                )
            else:
                game = HeadToHeadEvaluator(
                    self.first_engine,
                    self.second_engine,
                    first_model_id=self.first_model_id,
                    second_model_id=self.second_model_id,
                    rules=self.rules,
                    max_plies=self.max_plies,
                ).play_game(setup=setup)
            results.append(game)
        return EvaluationSummary(self.first_model_id, self.second_model_id, tuple(results))


def _swap_status(status: GameStatus) -> GameStatus:
    if status is GameStatus.CHO_WIN:
        return GameStatus.HAN_WIN
    if status is GameStatus.HAN_WIN:
        return GameStatus.CHO_WIN
    return status
