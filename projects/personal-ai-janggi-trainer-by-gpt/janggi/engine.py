from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

from .core import GameState, Move, Side


@dataclass(frozen=True)
class EngineInfo:
    """Engine metadata exposed without coupling callers to a concrete engine."""

    name: str
    version: Optional[str] = None
    author: Optional[str] = None


@dataclass(frozen=True)
class EngineAnalysis:
    """Engine analysis result using a backend-neutral representation."""

    best_move: Optional[Move] = None
    score_cp: Optional[int] = None
    depth: Optional[int] = None
    nodes: Optional[int] = None
    principal_variation: tuple[Move, ...] = ()
    perspective: Side = Side.CHO


class Engine(Protocol):
    """Protocol implemented by every Janggi move/analysis backend."""

    @property
    def info(self) -> EngineInfo:
        ...

    def choose_move(self, state: GameState) -> Move:
        """Return one legal move for the side to move."""
        ...

    def analyze(self, state: GameState) -> EngineAnalysis:
        """Return backend-neutral analysis for the current position."""
        ...


class FirstLegalEngine:
    """Minimal deterministic engine used for adapter integration tests.

    This is intentionally not an AI-strength implementation. It proves that the
    application can depend on the Engine protocol without depending on a specific
    engine package or executable.
    """

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(name="first-legal", version="1")

    def choose_move(self, state: GameState) -> Move:
        legal_moves = state.legal_moves(include_pass=False)
        if not legal_moves:
            if state.legal_moves(include_pass=True):
                return Move.pass_move()
            raise ValueError("position has no legal move")
        return legal_moves[0]

    def analyze(self, state: GameState) -> EngineAnalysis:
        move = self.choose_move(state) if state.legal_moves(include_pass=True) else None
        return EngineAnalysis(best_move=move, perspective=state.turn)


def validate_engine_move(engine: Engine, state: GameState, move: Move) -> Move:
    """Validate an engine-produced move against the authoritative domain model."""
    if not state.is_legal(move):
        raise ValueError(f"engine returned an illegal move: {move!r}")
    return move


def principal_variation_is_legal(state: GameState, moves: Sequence[Move]) -> bool:
    """Return whether every move in a proposed PV is legal from the given state."""
    current = state
    for move in moves:
        if not current.is_legal(move):
            return False
        current = current.apply(move)
    return True


def validate_engine_analysis(state: GameState, analysis: object) -> EngineAnalysis:
    """Normalize engine analysis against authoritative move legality.

    If the backend does not return an EngineAnalysis object, the result is
    degraded to an empty analysis for the current side to move. Illegal best moves
    are suppressed; malformed or illegal principal variations, variations without
    a usable best move, and variations whose first move disagrees with the best
    move are removed rather than allowing inconsistent backend data into
    presentation layers.
    """
    if not isinstance(analysis, EngineAnalysis):
        return EngineAnalysis(perspective=state.turn)

    perspective = analysis.perspective
    if not isinstance(perspective, Side):
        return EngineAnalysis(perspective=state.turn)

    score_cp = analysis.score_cp if _valid_optional_int(analysis.score_cp) else None
    depth = analysis.depth if _valid_non_negative_int(analysis.depth) else None
    nodes = analysis.nodes if _valid_non_negative_int(analysis.nodes) else None
    best_move = analysis.best_move
    if best_move is not None and not state.is_legal(best_move):
        best_move = None

    raw_principal_variation = analysis.principal_variation
    try:
        principal_variation = tuple(raw_principal_variation) if raw_principal_variation is not None else ()
    except TypeError:
        principal_variation = ()
    if principal_variation and not principal_variation_is_legal(state, principal_variation):
        principal_variation = ()
    elif principal_variation and best_move is None:
        principal_variation = ()
    elif best_move is not None and principal_variation and principal_variation[0] != best_move:
        principal_variation = ()

    return EngineAnalysis(
        best_move=best_move,
        score_cp=score_cp,
        depth=depth,
        nodes=nodes,
        principal_variation=principal_variation,
        perspective=analysis.perspective,
    )

def _valid_optional_int(value: object) -> bool:
    return value is None or (isinstance(value, int) and not isinstance(value, bool))


def _valid_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
