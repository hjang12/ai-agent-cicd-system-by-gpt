from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .coaching import CoachingReason, CoachingSeverity
from .core import GameState, Move, Side
from .review import CoachingReview, ReviewEntry


DEFAULT_PROBLEM_LIMIT = 5
MAX_PROBLEM_LIMIT = 20


@dataclass(frozen=True)
class PositionTrainingProblem:
    problem_id: str
    ply: int
    state: GameState
    side: Side
    target_move: Move
    original_move: Move
    severity: CoachingSeverity
    reason_codes: tuple[CoachingReason, ...]
    prompt: str
    explanation: str
    next_action: str

    def __post_init__(self) -> None:
        if not self.state.legal_moves(include_pass=True):
            raise ValueError("training problem state has no legal moves")
        if self.state.turn is not self.side:
            raise ValueError("training problem side must match state turn")
        try:
            self.state.apply(self.target_move)
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError("training problem target move must be legal") from exc


def generate_training_problems(
    review: CoachingReview,
    *,
    max_problems: int = DEFAULT_PROBLEM_LIMIT,
) -> tuple[PositionTrainingProblem, ...]:
    """Convert bounded review evidence into replayable position problems."""
    if (
        not isinstance(max_problems, int)
        or isinstance(max_problems, bool)
        or not 1 <= max_problems <= MAX_PROBLEM_LIMIT
    ):
        raise ValueError(f"max_problems must be between 1 and {MAX_PROBLEM_LIMIT}")

    candidates = [
        entry
        for entry in review.entries
        if entry.insight.severity in {
            CoachingSeverity.ACCEPTABLE,
            CoachingSeverity.INACCURACY,
            CoachingSeverity.MAJOR_MISTAKE,
        }
        and entry.analysis.recommended_move is not None
    ]
    selected = candidates[-max_problems:][::-1]
    return tuple(_problem_from_entry(entry) for entry in selected)


def _problem_from_entry(entry: ReviewEntry) -> PositionTrainingProblem:
    target_move = entry.analysis.recommended_move
    if target_move is None:
        raise ValueError("review entry has no target recommendation")

    return PositionTrainingProblem(
        problem_id=f"ply-{entry.ply}",
        ply=entry.ply,
        state=entry.state,
        side=entry.side,
        target_move=target_move,
        original_move=entry.move,
        severity=entry.insight.severity,
        reason_codes=entry.insight.reason_codes,
        prompt=_prompt_for(entry),
        explanation=entry.insight.message,
        next_action=entry.insight.next_action,
    )


def _prompt_for(entry: ReviewEntry) -> str:
    if CoachingReason.HANGING_PIECE in entry.insight.reason_codes:
        return "같은 포지션에서 기물이 잡히지 않도록 더 나은 수를 찾아보세요."
    if CoachingReason.IMMEDIATE_CAPTURE in entry.insight.reason_codes:
        return "같은 포지션에서 교환과 되잡기까지 생각해 더 나은 수를 찾아보세요."
    if CoachingReason.DOUBLE_ATTACK in entry.insight.reason_codes:
        return "같은 포지션에서 상대의 두 기물 공격 가능성을 막는 수를 찾아보세요."
    return "같은 포지션에서 현재 기준 추천수를 찾아보세요."
