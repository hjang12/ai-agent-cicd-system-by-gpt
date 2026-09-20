from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .analysis import Analyzer, MoveAnalysis
from .coaching import CoachingInsight, CoachingReason, CoachingSeverity, coach_move
from .core import GameState, Move, Side
from .record import GameRecord


DEFAULT_REVIEW_LIMIT = 20
MAX_REVIEW_LIMIT = 60


@dataclass(frozen=True)
class ReviewEntry:
    ply: int
    side: Side
    move: Move
    analysis: MoveAnalysis
    insight: CoachingInsight


@dataclass(frozen=True)
class CoachingReview:
    total_moves: int
    reviewed_moves: int
    skipped_moves: int
    entries: tuple[ReviewEntry, ...]
    reason_counts: tuple[tuple[CoachingReason, int], ...]
    severity_counts: tuple[tuple[CoachingSeverity, int], ...]


def review_record(
    record: GameRecord,
    analyzer: Analyzer,
    *,
    max_moves: int = DEFAULT_REVIEW_LIMIT,
    side: Optional[Side] = None,
) -> CoachingReview:
    """Review recent record moves and aggregate stable coaching signals."""
    if not 1 <= max_moves <= MAX_REVIEW_LIMIT:
        raise ValueError(f"max_moves must be between 1 and {MAX_REVIEW_LIMIT}")

    candidates: list[tuple[int, Side, Move, GameState]] = []
    state = GameState.initial(record.setup)

    for index, move in enumerate(record.moves):
        move_side = state.turn
        if side is None or move_side is side:
            candidates.append((index + 1, move_side, move, state))
        state = state.apply(move)

    selected = candidates[-max_moves:]
    entries: list[ReviewEntry] = []
    reason_counts = {reason: 0 for reason in CoachingReason}
    severity_counts = {severity: 0 for severity in CoachingSeverity}

    for ply, move_side, move, move_state in selected:
        analysis = analyzer.analyze_move(move_state, move)
        insight = coach_move(analysis)
        entries.append(ReviewEntry(
            ply=ply,
            side=move_side,
            move=move,
            analysis=analysis,
            insight=insight,
        ))
        severity_counts[insight.severity] += 1
        for reason in insight.reason_codes:
            reason_counts[reason] += 1

    return CoachingReview(
        total_moves=len(record.moves),
        reviewed_moves=len(entries),
        skipped_moves=max(0, len(candidates) - len(selected)),
        entries=tuple(entries),
        reason_counts=tuple((reason, count) for reason, count in reason_counts.items() if count),
        severity_counts=tuple((severity, count) for severity, count in severity_counts.items() if count),
    )
