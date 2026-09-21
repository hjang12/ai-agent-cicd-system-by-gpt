from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .core import GameState, Move, Side


class GameStatus(Enum):
    PLAYING = "playing"
    CHO_WIN = "cho_win"
    HAN_WIN = "han_win"
    DRAW_BIKJANG = "draw_bikjang"
    DRAW_REPETITION = "draw_repetition"
    DRAW_CONSECUTIVE_PASS = "draw_consecutive_pass"
    DRAW_STALEMATE = "draw_stalemate"


@dataclass(frozen=True)
class RuleSet:
    """Match-policy knobs kept separate from piece movement."""

    bikjang_is_draw: bool = True
    repetition_limit: Optional[int] = None
    consecutive_passes_for_draw: Optional[int] = 2

    def __post_init__(self) -> None:
        if self.repetition_limit is not None and self.repetition_limit < 2:
            raise ValueError("repetition_limit must be at least 2 when enabled")
        if self.consecutive_passes_for_draw is not None and self.consecutive_passes_for_draw < 2:
            raise ValueError("consecutive_passes_for_draw must be at least 2 when enabled")


@dataclass(frozen=True)
class Match:
    state: GameState
    setup: str = "classic"
    rules: RuleSet = RuleSet()

    @classmethod
    def new(cls, setup: str = "classic", rules: Optional[RuleSet] = None) -> "Match":
        return cls(GameState.initial(setup, starting_side=Side.HAN), setup, rules or RuleSet())

    @property
    def status(self) -> GameStatus:
        if self.rules.bikjang_is_draw and self.state.is_bikjang():
            return GameStatus.DRAW_BIKJANG

        if (
            self.rules.repetition_limit is not None
            and self.position_repetition_count() >= self.rules.repetition_limit
        ):
            return GameStatus.DRAW_REPETITION

        if (
            self.rules.consecutive_passes_for_draw is not None
            and self.consecutive_pass_count() >= self.rules.consecutive_passes_for_draw
        ):
            return GameStatus.DRAW_CONSECUTIVE_PASS

        legal_moves = self.state.legal_moves(include_pass=True)
        if legal_moves:
            return GameStatus.PLAYING

        if self.state.is_in_check(self.state.turn):
            return _win_status(self.state.turn.opponent)
        return GameStatus.DRAW_STALEMATE

    def play(self, move: Move) -> "Match":
        if self.status is not GameStatus.PLAYING:
            raise ValueError(f"match is already finished: {self.status.value}")
        return Match(state=self.state.apply(move), setup=self.setup, rules=self.rules)

    def undo(self) -> "Match":
        """Return a new match with the most recent move removed."""
        if not self.state.history:
            raise ValueError("match has no moves to undo")
        replay = GameState.initial(self.setup, starting_side=Side.HAN)
        for move in self.state.history[:-1]:
            replay = replay.apply(move)
        return Match(state=replay, setup=self.setup, rules=self.rules)

    def legal_moves(self) -> tuple[Move, ...]:
        if self.status is not GameStatus.PLAYING:
            return ()
        return self.state.legal_moves(include_pass=True)

    def position_repetition_count(self) -> int:
        """Count occurrences of the current position from the starting position."""
        current = self.state.position_key()
        replay = GameState.initial(self.setup, starting_side=Side.HAN)
        count = 1 if replay.position_key() == current else 0
        for move in self.state.history:
            replay = replay.apply(move)
            if replay.position_key() == current:
                count += 1
        return count

    def consecutive_pass_count(self) -> int:
        count = 0
        for move in reversed(self.state.history):
            if not move.is_pass:
                break
            count += 1
        return count


def _win_status(side: Side) -> GameStatus:
    return GameStatus.CHO_WIN if side is Side.CHO else GameStatus.HAN_WIN
