from __future__ import annotations

from dataclasses import dataclass

from .coaching import CoachingReason


@dataclass(frozen=True)
class TrainingMetricsSnapshot:
    attempts: int
    correct: int
    incorrect: int
    unique_problems: int
    accuracy: float
    problem_attempts: tuple[tuple[str, int], ...]
    problem_incorrect: tuple[tuple[str, int], ...]
    reason_attempts: tuple[tuple[CoachingReason, int], ...]
    reason_correct: tuple[tuple[CoachingReason, int], ...]


class TrainingSessionMetrics:
    """Ephemeral metrics for one running trainer session."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._attempts = 0
        self._correct = 0
        self._problem_ids: set[str] = set()
        self._problem_attempts: dict[str, int] = {}
        self._problem_incorrect: dict[str, int] = {}
        self._reason_attempts = {reason: 0 for reason in CoachingReason}
        self._reason_correct = {reason: 0 for reason in CoachingReason}

    def record_attempt(
        self,
        *,
        problem_id: str,
        correct: bool,
        reason_codes: tuple[CoachingReason, ...],
    ) -> None:
        if not isinstance(problem_id, str) or not problem_id:
            raise ValueError("problem_id must be a non-empty string")
        if not isinstance(correct, bool):
            raise ValueError("correct must be boolean")
        self._attempts += 1
        if correct:
            self._correct += 1
        self._problem_ids.add(problem_id)
        self._problem_attempts[problem_id] = self._problem_attempts.get(problem_id, 0) + 1
        if not correct:
            self._problem_incorrect[problem_id] = self._problem_incorrect.get(problem_id, 0) + 1
        for reason in reason_codes:
            self._reason_attempts[reason] += 1
            if correct:
                self._reason_correct[reason] += 1

    def snapshot(self) -> TrainingMetricsSnapshot:
        incorrect = self._attempts - self._correct
        accuracy = self._correct / self._attempts if self._attempts else 0.0
        return TrainingMetricsSnapshot(
            attempts=self._attempts,
            correct=self._correct,
            incorrect=incorrect,
            unique_problems=len(self._problem_ids),
            accuracy=accuracy,
            problem_attempts=tuple(
                sorted(self._problem_attempts.items())
            ),
            problem_incorrect=tuple(
                sorted(self._problem_incorrect.items())
            ),
            reason_attempts=tuple(
                (reason, count)
                for reason, count in self._reason_attempts.items()
                if count
            ),
            reason_correct=tuple(
                (reason, count)
                for reason, count in self._reason_correct.items()
                if count
            ),
        )
