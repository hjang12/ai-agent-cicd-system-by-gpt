from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .core import GameState, Move, PieceType, Side
from .engine import Engine, EngineAnalysis, validate_engine_analysis, validate_engine_move


class TacticalRisk(str, Enum):
    """Domain-level immediate tactical risk detected without engine assumptions."""

    NONE = "none"
    IMMEDIATE_CAPTURE = "immediate_capture"
    HANGING_PIECE = "hanging_piece"


class TacticalMotif(str, Enum):
    """Bounded tactical motifs surfaced separately from engine score."""

    DOUBLE_ATTACK = "double_attack"


PIECE_TACTICAL_VALUE = {
    PieceType.GENERAL: 10_000,
    PieceType.CHARIOT: 1_000,
    PieceType.CANNON: 700,
    PieceType.ELEPHANT: 500,
    PieceType.HORSE: 500,
    PieceType.GUARD: 300,
    PieceType.SOLDIER: 100,
}


@dataclass(frozen=True)
class MoveAnalysis:
    """Analysis of one played move from the moving side's perspective."""

    move: Move
    recommended_move: Optional[Move]
    score_before_cp: Optional[int]
    score_after_cp: Optional[int]
    score_delta_cp: Optional[int]
    depth: Optional[int]
    nodes: Optional[int]
    principal_variation: tuple[Move, ...] = ()
    perspective: Side = Side.CHO
    moved_piece: Optional[PieceType] = None
    captured_piece: Optional[PieceType] = None
    gives_check: bool = False
    destination_attacked: bool = False
    tactical_risk: TacticalRisk = TacticalRisk.NONE
    tactical_motifs: tuple[TacticalMotif, ...] = ()

    @property
    def is_best_move(self) -> Optional[bool]:
        if self.recommended_move is None:
            return None
        return self.move == self.recommended_move


class Analyzer:
    """Build a stable analysis result around a pluggable engine backend."""

    def __init__(self, engine: Engine, *, include_tactical_motifs: bool = True) -> None:
        self.engine = engine
        self.include_tactical_motifs = include_tactical_motifs

    def analyze_move(self, state: GameState, move: Move) -> MoveAnalysis:
        validate_engine_move(self.engine, state, move)
        moved_piece = None
        captured_piece = None
        if not move.is_pass and move.src is not None:
            source = state.piece_at(move.src)
            moved_piece = source.kind if source is not None else None
        if not move.is_pass and move.dst is not None:
            target = state.piece_at(move.dst)
            captured_piece = target.kind if target is not None else None
        before = validate_engine_analysis(state, self.engine.analyze(state))
        after_state = state.apply(move)
        gives_check = after_state.is_in_check(state.turn.opponent)
        destination_attacked, tactical_risk = _destination_risk(after_state, move, state.turn)
        tactical_motifs = (
            _tactical_motifs(after_state, move, state.turn)
            if self.include_tactical_motifs
            else ()
        )
        after = validate_engine_analysis(after_state, self.engine.analyze(after_state))
        score_after = _score_from_mover_perspective(after, state.turn)
        score_before = _score_from_mover_perspective(before, state.turn)
        score_delta = _score_delta(score_before, score_after)
        return MoveAnalysis(
            move=move,
            recommended_move=before.best_move,
            score_before_cp=score_before,
            score_after_cp=score_after,
            score_delta_cp=score_delta,
            depth=before.depth,
            nodes=before.nodes,
            principal_variation=before.principal_variation,
            perspective=state.turn,
            moved_piece=moved_piece,
            captured_piece=captured_piece,
            gives_check=gives_check,
            destination_attacked=destination_attacked,
            tactical_risk=tactical_risk,
            tactical_motifs=tactical_motifs,
        )

    def analyze_position(self, state: GameState) -> EngineAnalysis:
        """Expose validated backend-neutral position analysis for callers without a move."""
        return validate_engine_analysis(state, self.engine.analyze(state))


def _destination_risk(
    state: GameState,
    move: Move,
    mover: Side,
) -> tuple[bool, TacticalRisk]:
    """Detect immediate capture risk and whether the moved piece is left hanging."""
    if move.is_pass or move.dst is None:
        return False, TacticalRisk.NONE

    destination = move.dst
    capture_moves = [
        candidate
        for candidate in state.legal_moves(include_pass=False)
        if candidate.dst == destination
    ]
    if not capture_moves:
        return False, TacticalRisk.NONE

    for capture in capture_moves:
        captured_state = state.apply(capture)
        recapture_exists = any(
            response.dst == destination
            for response in captured_state.legal_moves(include_pass=False)
            if captured_state.piece_at(response.src) is not None
            and captured_state.piece_at(response.src).side is mover
        )
        if not recapture_exists:
            return True, TacticalRisk.HANGING_PIECE

    return True, TacticalRisk.IMMEDIATE_CAPTURE


def _tactical_motifs(
    state: GameState,
    move: Move,
    mover: Side,
) -> tuple[TacticalMotif, ...]:
    """Detect a bounded next-turn double-attack threat.

    The played move is followed by one opponent reply. We then restore the
    mover's turn and look for legal captures against at least two sufficiently
    valuable opposing pieces. The mover's intervening defensive resources are
    intentionally ignored, so this remains a forward-looking heuristic.
    """
    if move.is_pass or move.dst is None:
        return ()

    opponent = mover.opponent
    for reply in state.legal_moves(include_pass=False):
        reply_state = state.apply(reply)
        future_mover_state = GameState(
            board=reply_state.board,
            turn=mover,
            history=reply_state.history,
        )
        target_squares: set[tuple[int, int]] = set()
        for future_capture in future_mover_state.legal_moves(include_pass=False):
            if future_capture.dst is None:
                continue
            target = future_mover_state.piece_at(future_capture.dst)
            if target is None or target.side is not opponent or target.kind is PieceType.GENERAL:
                continue
            if PIECE_TACTICAL_VALUE[target.kind] >= PIECE_TACTICAL_VALUE[PieceType.GUARD]:
                target_squares.add(future_capture.dst)
        if len(target_squares) >= 2:
            return (TacticalMotif.DOUBLE_ATTACK,)

    return ()


def _score_from_mover_perspective(analysis: EngineAnalysis, mover: Side) -> Optional[int]:
    if analysis.score_cp is None:
        return None
    return analysis.score_cp if analysis.perspective is mover else -analysis.score_cp


def _score_delta(before: Optional[int], after: Optional[int]) -> Optional[int]:
    if before is None or after is None:
        return None
    return after - before
