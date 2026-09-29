from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite
from typing import Any, Protocol, Sequence

from .core import GameState, Move, PieceType, Side, palace_for
from .training import TrainingDataset


VALUE_MODEL_SCORE_LIMIT = 100_000
LINEAR_VALUE_MODEL_FORMAT = "janggi-linear-value-v1"
DEFAULT_TARGET_SCALE_CP = 3_000.0
DEFAULT_RIDGE = 1.0


class ValueModel(Protocol):
    """Backend-neutral value model consumed by NegamaxEngine.

    The model predicts a centipawn-like integer from the side-to-move perspective.
    The search layer removes move history before calling the model so the model
    follows the same board-and-turn identity used by the evaluation cache.
    """

    def predict_cp(self, state: GameState) -> int:
        """Return the position value from state.turn's perspective."""
        ...


FEATURE_NAMES: tuple[str, ...] = (
    "material_balance",
    "chariot_balance",
    "cannon_balance",
    "horse_balance",
    "elephant_balance",
    "guard_balance",
    "soldier_balance",
    "soldier_progress",
    "center_control",
    "mobility_balance",
    "general_mobility",
    "palace_pressure",
    "check_pressure",
)


def validate_value_score(score: int) -> int:
    """Validate a model score while reserving the search mate-score range."""
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("value model score must be an integer")
    if not -VALUE_MODEL_SCORE_LIMIT < score < VALUE_MODEL_SCORE_LIMIT:
        raise ValueError("value model score must stay below the reserved mate-score range")
    return score


def extract_value_features(state: GameState) -> tuple[float, ...]:
    """Extract a deterministic, history-independent feature vector.

    Every feature is measured from the side-to-move perspective and bounded to
    a compact numeric range so a linear model can be trained without external
    numerical dependencies.
    """
    if not isinstance(state, GameState):
        raise ValueError("state must be a GameState")

    own_counts = {kind: 0 for kind in PieceType}
    opp_counts = {kind: 0 for kind in PieceType}
    own_material = 0
    opp_material = 0
    own_soldier_progress = 0.0
    opp_soldier_progress = 0.0
    own_center = 0.0
    opp_center = 0.0

    piece_values = {
        PieceType.GENERAL: 10_000,
        PieceType.CHARIOT: 1_300,
        PieceType.CANNON: 700,
        PieceType.ELEPHANT: 300,
        PieceType.HORSE: 500,
        PieceType.GUARD: 300,
        PieceType.SOLDIER: 200,
    }

    for y in range(10):
        for x in range(9):
            piece = state.piece_at((x, y))
            if piece is None:
                continue
            own = piece.side is state.turn
            counts = own_counts if own else opp_counts
            counts[piece.kind] += 1
            if own:
                own_material += piece_values[piece.kind]
            else:
                opp_material += piece_values[piece.kind]

            if piece.kind is PieceType.SOLDIER:
                progress = y if piece.side is Side.CHO else 9 - y
                if own:
                    own_soldier_progress += progress
                else:
                    opp_soldier_progress += progress

            center_weight = 1.0 if x == 4 else 0.5 if x in (3, 5) else 0.0
            if own:
                own_center += center_weight
            else:
                opp_center += center_weight

    max_material = 2 * 1_300 + 2 * 700 + 2 * 500 + 2 * 300 + 2 * 300 + 5 * 200
    material_balance = _clip((own_material - opp_material) / max_material, -1.0, 1.0)

    max_counts = {
        PieceType.CHARIOT: 2,
        PieceType.CANNON: 2,
        PieceType.HORSE: 2,
        PieceType.ELEPHANT: 2,
        PieceType.GUARD: 2,
        PieceType.SOLDIER: 5,
    }
    count_features = tuple(
        _clip(
            (own_counts[kind] - opp_counts[kind]) / max_counts[kind],
            -1.0,
            1.0,
        )
        for kind in (
            PieceType.CHARIOT,
            PieceType.CANNON,
            PieceType.HORSE,
            PieceType.ELEPHANT,
            PieceType.GUARD,
            PieceType.SOLDIER,
        )
    )

    soldier_progress = _clip(
        (own_soldier_progress - opp_soldier_progress) / 45.0,
        -1.0,
        1.0,
    )
    center_control = _clip((own_center - opp_center) / 8.0, -1.0, 1.0)

    own_moves = state.legal_moves(include_pass=False)
    opponent_state = GameState(board=state.board, turn=state.turn.opponent)
    opp_moves = opponent_state.legal_moves(include_pass=False)

    mobility_balance = _clip((len(own_moves) - len(opp_moves)) / 50.0, -1.0, 1.0)

    own_general = state.find_general(state.turn)
    opp_general = state.find_general(state.turn.opponent)
    own_general_moves = _count_general_moves(own_moves, own_general)
    opp_general_moves = _count_general_moves(opp_moves, opp_general)
    general_mobility = _clip((own_general_moves - opp_general_moves) / 8.0, -1.0, 1.0)

    opponent_palace = palace_for(state.turn.opponent)
    own_palace = palace_for(state.turn)
    own_palace_pressure = sum(1 for move in own_moves if move.dst in opponent_palace)
    opp_palace_pressure = sum(1 for move in opp_moves if move.dst in own_palace)
    palace_pressure = _clip(
        (own_palace_pressure - opp_palace_pressure) / 12.0,
        -1.0,
        1.0,
    )

    check_pressure = (
        (1.0 if state.is_in_check(state.turn.opponent) else 0.0)
        - (1.0 if state.is_in_check(state.turn) else 0.0)
    )

    return (
        material_balance,
        *count_features,
        soldier_progress,
        center_control,
        mobility_balance,
        general_mobility,
        palace_pressure,
        check_pressure,
    )


@dataclass(frozen=True)
class LinearValueModel:
    """Dependency-free linear evaluator implementing the ValueModel protocol."""

    weights: tuple[float, ...]
    bias: float = 0.0
    target_scale_cp: float = DEFAULT_TARGET_SCALE_CP

    def __post_init__(self) -> None:
        if len(self.weights) != len(FEATURE_NAMES):
            raise ValueError(
                f"linear value model requires {len(FEATURE_NAMES)} weights"
            )
        if not all(isinstance(weight, (int, float)) and not isinstance(weight, bool) for weight in self.weights):
            raise ValueError("linear value model weights must be numeric")
        if not all(isfinite(float(weight)) for weight in self.weights):
            raise ValueError("linear value model weights must be finite")
        if not isinstance(self.bias, (int, float)) or isinstance(self.bias, bool) or not isfinite(float(self.bias)):
            raise ValueError("linear value model bias must be finite")
        if (
            not isinstance(self.target_scale_cp, (int, float))
            or isinstance(self.target_scale_cp, bool)
            or not isfinite(float(self.target_scale_cp))
            or self.target_scale_cp <= 0
        ):
            raise ValueError("target_scale_cp must be a positive finite number")

    def predict_cp(self, state: GameState) -> int:
        features = extract_value_features(state)
        raw_score = float(self.bias) + sum(
            float(weight) * feature
            for weight, feature in zip(self.weights, features)
        )
        bounded_score = max(
            -(VALUE_MODEL_SCORE_LIMIT - 1),
            min(VALUE_MODEL_SCORE_LIMIT - 1, raw_score),
        )
        return validate_value_score(int(round(bounded_score)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": LINEAR_VALUE_MODEL_FORMAT,
            "feature_names": list(FEATURE_NAMES),
            "weights": [float(weight) for weight in self.weights],
            "bias": float(self.bias),
            "target_scale_cp": float(self.target_scale_cp),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LinearValueModel":
        if not isinstance(data, dict) or data.get("format") != LINEAR_VALUE_MODEL_FORMAT:
            raise ValueError("unsupported linear value model format")
        feature_names = data.get("feature_names")
        if feature_names != list(FEATURE_NAMES):
            raise ValueError("linear value model feature names do not match current schema")
        raw_weights = data.get("weights")
        if (
            not isinstance(raw_weights, list)
            or len(raw_weights) != len(FEATURE_NAMES)
            or not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in raw_weights)
        ):
            raise ValueError("linear value model weights must match the feature schema")
        bias = data.get("bias", 0.0)
        target_scale_cp = data.get("target_scale_cp", DEFAULT_TARGET_SCALE_CP)
        return cls(
            weights=tuple(float(value) for value in raw_weights),
            bias=float(bias),
            target_scale_cp=float(target_scale_cp),
        )

    @classmethod
    def from_json(cls, text: str) -> "LinearValueModel":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("linear value model JSON must contain an object")
        return cls.from_dict(data)


class LinearValueTrainer:
    """Fit a linear value model with dependency-free ridge regression."""

    def __init__(
        self,
        *,
        ridge: float = DEFAULT_RIDGE,
        target_scale_cp: float = DEFAULT_TARGET_SCALE_CP,
    ) -> None:
        try:
            ridge_value = float(ridge)
            target_scale_value = float(target_scale_cp)
        except (TypeError, ValueError) as exc:
            raise ValueError("ridge and target_scale_cp must be numeric") from exc
        if ridge_value < 0 or not isfinite(ridge_value):
            raise ValueError("ridge must be a non-negative finite number")
        if target_scale_value <= 0 or not isfinite(target_scale_value):
            raise ValueError("target_scale_cp must be a positive finite number")
        self.ridge = ridge_value
        self.target_scale_cp = target_scale_value

    def fit(self, dataset: TrainingDataset) -> LinearValueModel:
        if not isinstance(dataset, TrainingDataset):
            raise ValueError("dataset must be a TrainingDataset")
        if not dataset.examples:
            raise ValueError("cannot train linear value model from an empty dataset")

        dimension = len(FEATURE_NAMES) + 1
        normal = [[0.0 for _ in range(dimension)] for _ in range(dimension)]
        target = [0.0 for _ in range(dimension)]

        for example in dataset.examples:
            features = extract_value_features(example.state)
            row = [1.0, *features]
            y = float(example.outcome.value) * self.target_scale_cp
            for row_index in range(dimension):
                target[row_index] += row[row_index] * y
                for col_index in range(dimension):
                    normal[row_index][col_index] += row[row_index] * row[col_index]

        for index in range(1, dimension):
            normal[index][index] += self.ridge

        solution = _solve_linear_system(normal, target)
        return LinearValueModel(
            weights=tuple(solution[1:]),
            bias=solution[0],
            target_scale_cp=self.target_scale_cp,
        )


def _count_general_moves(
    moves: Sequence[Move],
    position: tuple[int, int] | None,
) -> int:
    if position is None:
        return 0
    return sum(1 for move in moves if move.src == position)


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Solve a small dense linear system using Gaussian elimination."""
    size = len(vector)
    if len(matrix) != size or any(len(row) != size for row in matrix):
        raise ValueError("linear system dimensions do not match")

    augmented = [list(row) + [vector[index]] for index, row in enumerate(matrix)]

    for pivot_column in range(size):
        pivot_row = max(
            range(pivot_column, size),
            key=lambda row_index: abs(augmented[row_index][pivot_column]),
        )
        pivot_value = augmented[pivot_row][pivot_column]
        if abs(pivot_value) < 1e-12:
            raise ValueError("linear system is singular; increase ridge regularization")

        if pivot_row != pivot_column:
            augmented[pivot_column], augmented[pivot_row] = (
                augmented[pivot_row],
                augmented[pivot_column],
            )

        pivot_value = augmented[pivot_column][pivot_column]
        for column in range(pivot_column, size + 1):
            augmented[pivot_column][column] /= pivot_value

        for row_index in range(size):
            if row_index == pivot_column:
                continue
            factor = augmented[row_index][pivot_column]
            if abs(factor) < 1e-15:
                continue
            for column in range(pivot_column, size + 1):
                augmented[row_index][column] -= factor * augmented[pivot_column][column]

    return [augmented[index][size] for index in range(size)]
