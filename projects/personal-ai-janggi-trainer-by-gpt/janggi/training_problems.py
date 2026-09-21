from __future__ import annotations

from dataclasses import dataclass

from .coaching import CoachingReason, CoachingSeverity
from .core import GameState, Move, Side
from .review import CoachingReview, ReviewEntry
from .training_metrics import TrainingMetricsSnapshot


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


def adaptive_reason_priority(
    metrics: TrainingMetricsSnapshot,
) -> tuple[CoachingReason, ...]:
    """Return observed mistake reasons ordered from lowest session accuracy upward."""
    attempts = dict(metrics.reason_attempts)
    correct = dict(metrics.reason_correct)
    ranked: list[tuple[CoachingReason, float, int, int]] = []

    for reason, count in attempts.items():
        if count <= 0:
            continue
        correct_count = correct.get(reason, 0)
        incorrect = max(count - correct_count, 0)
        if incorrect <= 0:
            continue
        accuracy = correct_count / count
        ranked.append((reason, accuracy, incorrect, count))

    ranked.sort(key=lambda item: (item[1], -item[2], -item[3], item[0].value))
    return tuple(item[0] for item in ranked)


def adaptive_problem_priority(
    metrics: TrainingMetricsSnapshot,
) -> tuple[str, ...]:
    """Return repeatedly missed problem ids ordered by observed miss count."""
    attempts = dict(metrics.problem_attempts)
    incorrect = dict(metrics.problem_incorrect)
    ranked = [
        (problem_id, incorrect_count, attempts.get(problem_id, 0))
        for problem_id, incorrect_count in incorrect.items()
        if incorrect_count > 0
    ]
    ranked.sort(key=lambda item: (-item[1], -item[2], item[0]))
    return tuple(problem_id for problem_id, _, _ in ranked)


def select_adaptive_training_problems(
    problems: tuple[PositionTrainingProblem, ...],
    metrics: TrainingMetricsSnapshot,
    *,
    max_problems: int = DEFAULT_PROBLEM_LIMIT,
) -> tuple[PositionTrainingProblem, ...]:
    """Prioritize repeated mistakes, then low-accuracy reason signals.

    The selector only reorders the provided problems and never creates new
    training evidence. When no adaptive evidence exists, recent-first order
    is preserved.
    """
    if (
        not isinstance(max_problems, int)
        or isinstance(max_problems, bool)
        or not 1 <= max_problems <= MAX_PROBLEM_LIMIT
    ):
        raise ValueError(f"max_problems must be between 1 and {MAX_PROBLEM_LIMIT}")

    priority_problems = adaptive_problem_priority(metrics)
    priority_problem_rank = {
        problem_id: index
        for index, problem_id in enumerate(priority_problems)
    }
    priority_reasons = adaptive_reason_priority(metrics)
    priority_reason_rank = {
        reason: index for index, reason in enumerate(priority_reasons)
    }

    if not priority_problem_rank and not priority_reason_rank:
        return problems[:max_problems]

    def selection_key(indexed_problem: tuple[int, PositionTrainingProblem]) -> tuple[int, int, int, int]:
        index, problem = indexed_problem
        problem_rank = priority_problem_rank.get(problem.problem_id)
        matching_ranks = [
            priority_reason_rank[reason]
            for reason in problem.reason_codes
            if reason in priority_reason_rank
        ]
        if problem_rank is not None:
            return (0, problem_rank, min(matching_ranks, default=len(priority_reason_rank)), index)
        return (1, len(priority_problem_rank), min(matching_ranks, default=len(priority_reason_rank)), index)

    ordered = sorted(enumerate(problems), key=selection_key)
    return tuple(problem for _, problem in ordered[:max_problems])


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
