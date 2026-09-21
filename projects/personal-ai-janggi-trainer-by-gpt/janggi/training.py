from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Iterable, Optional

from .core import GameState, Move, Side
from .pipeline import RecordValidator, TrainingDisposition
from .record import GameRecord, state_from_dict, state_to_dict


class Outcome(Enum):
    LOSS = -1
    DRAW = 0
    WIN = 1


@dataclass(frozen=True)
class TrainingExample:
    """One position/action/value sample derived from a completed record."""

    state: GameState
    move: Move
    outcome: Outcome
    source: str
    setup: str = "classic"

    def __post_init__(self) -> None:
        if not isinstance(self.state, GameState):
            raise ValueError("training example state must be a GameState")
        if not isinstance(self.move, Move):
            raise ValueError("training example move must be a Move")
        if not isinstance(self.outcome, Outcome):
            raise ValueError("training example outcome must be an Outcome")
        try:
            self.state.apply(self.move)
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError("training example move is not legal in state") from exc
        if not isinstance(self.source, str):
            raise ValueError("training example source must be a string")
        if not isinstance(self.setup, str) or self.setup not in {"classic", "left", "right", "both"}:
            raise ValueError("invalid training example setup")

    @property
    def side_to_move(self) -> Side:
        return self.state.turn

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": state_to_dict(self.state, setup=self.setup),
            "move": _move_to_dict(self.move),
            "outcome": self.outcome.value,
            "source": self.source,
            "setup": self.setup,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrainingExample":
        if not isinstance(data, dict):
            raise ValueError("training example must be an object")
        state_data = data.get("state")
        if not isinstance(state_data, dict):
            raise ValueError("training example state must be an object")
        setup = data.get("setup", state_data.get("setup", "classic"))
        if not isinstance(setup, str) or setup not in {"classic", "left", "right", "both"}:
            raise ValueError("invalid training example setup")
        move = _move_from_dict(data.get("move"))
        try:
            outcome = Outcome(data["outcome"])
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid training outcome") from exc
        source = data.get("source")
        if not isinstance(source, str):
            raise ValueError("training example source must be a string")
        return cls(
            state=state_from_dict(state_data, setup=setup),
            move=move,
            outcome=outcome,
            source=source,
            setup=setup,
        )


@dataclass(frozen=True)
class TrainingDataset:
    """Immutable collection of position/action/value examples."""

    examples: tuple[TrainingExample, ...] = ()

    def __len__(self) -> int:
        return len(self.examples)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "janggi-training-v1",
            "examples": [example.to_dict() for example in self.examples],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrainingDataset":
        if not isinstance(data, dict) or data.get("format") != "janggi-training-v1":
            raise ValueError("unsupported training dataset format")
        raw_examples = data.get("examples", [])
        if not isinstance(raw_examples, list):
            raise ValueError("examples must be a list")
        return cls(tuple(TrainingExample.from_dict(item) for item in raw_examples))

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

    @classmethod
    def from_json(cls, text: str) -> "TrainingDataset":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("training dataset JSON must contain an object")
        return cls.from_dict(data)


class TrainingDatasetBuilder:
    """Convert accepted completed records into training-ready samples."""

    def __init__(self, validator: Optional[RecordValidator] = None) -> None:
        self.validator = validator or RecordValidator()

    def build(self, record: GameRecord) -> TrainingDataset:
        validation = self.validator.validate(record)
        if validation.training_disposition is not TrainingDisposition.CANDIDATE:
            return TrainingDataset()
        if validation.final_state is None or validation.terminal_status is None:
            return TrainingDataset()

        final_outcome = _outcome_for_cho(validation.terminal_status)
        examples: list[TrainingExample] = []
        state = GameState.initial(record.setup, starting_side=Side.HAN)
        for move in record.moves:
            examples.append(
                TrainingExample(
                    state=state,
                    move=move,
                    outcome=_outcome_for_side(final_outcome, state.turn),
                    source=record.source,
                    setup=record.setup,
                )
            )
            state = state.apply(move)
        return TrainingDataset(tuple(examples))

    def build_many(self, records: Iterable[GameRecord]) -> TrainingDataset:
        examples: list[TrainingExample] = []
        for record in records:
            examples.extend(self.build(record).examples)
        return TrainingDataset(tuple(examples))


def _outcome_for_cho(status: object) -> Outcome:
    value = getattr(status, "value", None)
    if value == "cho_win":
        return Outcome.WIN
    if value == "han_win":
        return Outcome.LOSS
    if isinstance(value, str) and value.startswith("draw_"):
        return Outcome.DRAW
    raise ValueError(f"unsupported terminal status for training: {status!r}")


def _outcome_for_side(cho_outcome: Outcome, side: Side) -> Outcome:
    if cho_outcome is Outcome.DRAW:
        return Outcome.DRAW
    if side is Side.CHO:
        return cho_outcome
    return Outcome.WIN if cho_outcome is Outcome.LOSS else Outcome.LOSS


def _move_to_dict(move: Move) -> dict[str, Any]:
    return {
        "pass": move.is_pass,
        "src": None if move.src is None else [move.src[0], move.src[1]],
        "dst": None if move.dst is None else [move.dst[0], move.dst[1]],
    }


def _move_from_dict(data: Any) -> Move:
    if not isinstance(data, dict):
        raise ValueError("training move must be an object")
    is_pass = data.get("pass", False)
    if not isinstance(is_pass, bool):
        raise ValueError("training move pass flag must be boolean")
    src = data.get("src")
    dst = data.get("dst")
    if is_pass:
        if src is not None or dst is not None:
            raise ValueError("pass move cannot contain src/dst")
        return Move.pass_move()
    if (
        not isinstance(src, list)
        or len(src) != 2
        or not all(isinstance(value, int) and not isinstance(value, bool) for value in src)
        or not isinstance(dst, list)
        or len(dst) != 2
        or not all(isinstance(value, int) and not isinstance(value, bool) for value in dst)
    ):
        raise ValueError("training normal move requires [x, y] src/dst")
    if not (0 <= src[0] < 9 and 0 <= src[1] < 10 and 0 <= dst[0] < 9 and 0 <= dst[1] < 10):
        raise ValueError("training move position out of bounds")
    return Move((src[0], src[1]), (dst[0], dst[1]))
