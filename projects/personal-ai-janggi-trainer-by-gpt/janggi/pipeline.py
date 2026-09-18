from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .core import GameState, Move, Position
from .match import GameStatus, Match, RuleSet
from .record import GameRecord


class RecordSource(Enum):
    PERSONAL = "personal"
    MANUAL = "manual"
    CURATED_HUMAN = "curated-human"
    SELF_PLAY = "self-play"
    UNKNOWN = "unknown"

    @classmethod
    def from_value(cls, value: object) -> "RecordSource":
        if not isinstance(value, str):
            return cls.UNKNOWN
        normalized = value.strip().lower()
        aliases = {
            "personal": cls.PERSONAL,
            "manual": cls.MANUAL,
            "curated-human": cls.CURATED_HUMAN,
            "curated_human": cls.CURATED_HUMAN,
            "self-play": cls.SELF_PLAY,
            "self_play": cls.SELF_PLAY,
        }
        return aliases.get(normalized, cls.UNKNOWN)


class ValidationStatus(Enum):
    VALID = "valid"
    INCOMPLETE = "incomplete"
    INVALID_STRUCTURE = "invalid_structure"
    INVALID_REPLAY = "invalid_replay"
    RESULT_MISSING = "result_missing"
    RESULT_MISMATCH = "result_mismatch"
    UNKNOWN_SOURCE = "unknown_source"


class TrainingDisposition(Enum):
    EXCLUDED = "excluded"
    CANDIDATE = "candidate"


@dataclass(frozen=True)
class RecordValidation:
    structural_valid: bool
    replay_valid: bool
    complete: bool
    status: ValidationStatus
    source_class: RecordSource
    terminal_status: Optional[GameStatus]
    result_status: Optional[GameStatus]
    result_consistent: bool
    analysis_eligible: bool
    training_disposition: TrainingDisposition
    issues: tuple[str, ...] = ()
    final_state: Optional[GameState] = None

    @property
    def training_eligible(self) -> bool:
        return self.training_disposition is TrainingDisposition.CANDIDATE


class RecordValidator:
    """Validate game records in layers without mutating the raw record."""

    def __init__(self, rules: Optional[RuleSet] = None) -> None:
        self.rules = rules or RuleSet()

    def validate(self, record: GameRecord) -> RecordValidation:
        if not isinstance(record, GameRecord):
            raise TypeError("record must be a GameRecord")

        issues: list[str] = []
        source_class = RecordSource.from_value(record.source)
        structural_valid = True

        if record.setup not in {"classic", "left", "right", "both"}:
            structural_valid = False
            issues.append("invalid_setup")

        if not isinstance(record.moves, tuple):
            structural_valid = False
            issues.append("moves_must_be_tuple")
        else:
            for index, move in enumerate(record.moves):
                if not isinstance(move, Move):
                    structural_valid = False
                    issues.append(f"invalid_move_type:{index}")
                    continue
                if move.is_pass:
                    if move.src is not None or move.dst is not None:
                        structural_valid = False
                        issues.append(f"invalid_pass_move:{index}")
                    continue
                if move.src is None or move.dst is None:
                    structural_valid = False
                    issues.append(f"incomplete_move:{index}")
                    continue
                if not _valid_position(move.src) or not _valid_position(move.dst):
                    structural_valid = False
                    issues.append(f"position_out_of_bounds:{index}")

        if record.result is not None and not isinstance(record.result, str):
            structural_valid = False
            issues.append("invalid_result_type")

        if not isinstance(record.source, str):
            structural_valid = False
            issues.append("invalid_source_type")

        if not structural_valid:
            return RecordValidation(
                structural_valid=False,
                replay_valid=False,
                complete=False,
                status=ValidationStatus.INVALID_STRUCTURE,
                source_class=source_class,
                terminal_status=None,
                result_status=None,
                result_consistent=False,
                analysis_eligible=False,
                training_disposition=TrainingDisposition.EXCLUDED,
                issues=tuple(issues),
            )

        try:
            final_state = record.replay()
        except (TypeError, ValueError, IndexError) as exc:
            issues.append(f"replay_error:{exc}")
            return RecordValidation(
                structural_valid=True,
                replay_valid=False,
                complete=False,
                status=ValidationStatus.INVALID_REPLAY,
                source_class=source_class,
                terminal_status=None,
                result_status=_parse_result(record.result),
                result_consistent=False,
                analysis_eligible=False,
                training_disposition=TrainingDisposition.EXCLUDED,
                issues=tuple(issues),
            )

        match = Match(state=final_state, setup=record.setup, rules=self.rules)
        terminal_status = match.status
        complete = terminal_status is not GameStatus.PLAYING
        result_status = _parse_result(record.result)
        result_consistent = True

        if source_class is RecordSource.UNKNOWN:
            issues.append("unknown_source")

        if not complete:
            status = ValidationStatus.INCOMPLETE
            if record.result is not None:
                result_consistent = False
                issues.append("result_on_incomplete_record")
            issues.append("game_not_terminal")
        elif record.result is None:
            result_consistent = False
            issues.append("result_missing")
            status = ValidationStatus.RESULT_MISSING
        elif result_status is None:
            result_consistent = False
            issues.append("unknown_result")
            status = ValidationStatus.RESULT_MISMATCH
        elif result_status is not terminal_status:
            result_consistent = False
            issues.append("result_mismatch")
            status = ValidationStatus.RESULT_MISMATCH
        elif source_class is RecordSource.UNKNOWN:
            status = ValidationStatus.UNKNOWN_SOURCE
        else:
            status = ValidationStatus.VALID

        training_disposition = self._training_disposition(
            source_class=source_class,
            complete=complete,
            result_consistent=result_consistent,
            replay_valid=True,
        )

        return RecordValidation(
            structural_valid=True,
            replay_valid=True,
            complete=complete,
            status=status,
            source_class=source_class,
            terminal_status=terminal_status,
            result_status=result_status,
            result_consistent=result_consistent,
            analysis_eligible=True,
            training_disposition=training_disposition,
            issues=tuple(issues),
            final_state=final_state,
        )

    def _training_disposition(
        self,
        *,
        source_class: RecordSource,
        complete: bool,
        result_consistent: bool,
        replay_valid: bool,
    ) -> TrainingDisposition:
        if not replay_valid or not complete or not result_consistent:
            return TrainingDisposition.EXCLUDED
        if source_class in {RecordSource.CURATED_HUMAN, RecordSource.SELF_PLAY}:
            return TrainingDisposition.CANDIDATE
        return TrainingDisposition.EXCLUDED


def _valid_position(pos: Position) -> bool:
    return (
        isinstance(pos, tuple)
        and len(pos) == 2
        and all(isinstance(value, int) and not isinstance(value, bool) for value in pos)
        and 0 <= pos[0] < 9
        and 0 <= pos[1] < 10
    )


def _parse_result(value: Optional[str]) -> Optional[GameStatus]:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    for status in GameStatus:
        if status.value == normalized or status.name.lower() == normalized:
            return status
    return None
