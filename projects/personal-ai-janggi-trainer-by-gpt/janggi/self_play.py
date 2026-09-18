from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .core import Move, Side
from .engine import Engine, validate_engine_move
from .match import GameStatus, Match, RuleSet
from .pipeline import RecordValidation, RecordValidator
from .record import GameRecord


@dataclass(frozen=True)
class SelfPlayResult:
    """One generated game plus the pipeline verdict for that generated record."""

    record: GameRecord
    validation: RecordValidation

    @property
    def training_eligible(self) -> bool:
        return self.validation.training_eligible


class SelfPlayGenerator:
    """Generate engine-vs-engine games using the authoritative Janggi rules."""

    def __init__(
        self,
        cho_engine: Engine,
        han_engine: Optional[Engine] = None,
        *,
        rules: Optional[RuleSet] = None,
        max_plies: int = 512,
        validator: Optional[RecordValidator] = None,
    ) -> None:
        if max_plies < 1:
            raise ValueError("max_plies must be at least 1")
        self.cho_engine = cho_engine
        self.han_engine = han_engine or cho_engine
        self.rules = rules or RuleSet()
        self.max_plies = max_plies
        self.validator = validator or RecordValidator(self.rules)

    def generate(self, setup: str = "classic") -> SelfPlayResult:
        match = Match.new(setup=setup, rules=self.rules)
        moves: list[Move] = []

        for _ in range(self.max_plies):
            if match.status is not GameStatus.PLAYING:
                break

            engine = self._engine_for(match.state.turn)
            proposed_move = engine.choose_move(match.state)
            move = validate_engine_move(engine, match.state, proposed_move)
            moves.append(move)
            match = match.play(move)

        status = match.status
        result = status.value if status is not GameStatus.PLAYING else None
        record = GameRecord(
            setup=setup,
            moves=tuple(moves),
            result=result,
            source="self-play",
        )
        validation = self.validator.validate(record)
        return SelfPlayResult(record=record, validation=validation)

    def generate_many(self, count: int, setup: str = "classic") -> tuple[SelfPlayResult, ...]:
        """Generate a batch of independent games with the configured engines."""
        if count < 1:
            raise ValueError("count must be at least 1")
        return tuple(self.generate(setup=setup) for _ in range(count))

    def _engine_for(self, side: Side) -> Engine:
        return self.cho_engine if side is Side.CHO else self.han_engine


def generate_self_play_game(
    cho_engine: Engine,
    han_engine: Optional[Engine] = None,
    *,
    setup: str = "classic",
    rules: Optional[RuleSet] = None,
    max_plies: int = 512,
) -> SelfPlayResult:
    """Convenience wrapper for one validated engine-vs-engine game."""
    return SelfPlayGenerator(
        cho_engine,
        han_engine,
        rules=rules,
        max_plies=max_plies,
    ).generate(setup=setup)


def generate_self_play_games(
    cho_engine: Engine,
    han_engine: Optional[Engine] = None,
    *,
    count: int,
    setup: str = "classic",
    rules: Optional[RuleSet] = None,
    max_plies: int = 512,
) -> tuple[SelfPlayResult, ...]:
    """Convenience wrapper for generating a validated batch of self-play games."""
    return SelfPlayGenerator(
        cho_engine,
        han_engine,
        rules=rules,
        max_plies=max_plies,
    ).generate_many(count=count, setup=setup)
