from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .analysis import MoveAnalysis, TacticalMotif, TacticalRisk
from .core import PieceType


class CoachingSeverity(str, Enum):
    """Stable user-facing classification built on the baseline engine score."""

    RECOMMENDED = "recommended"
    ACCEPTABLE = "acceptable"
    INACCURACY = "inaccuracy"
    MAJOR_MISTAKE = "major_mistake"
    UNAVAILABLE = "unavailable"


class CoachingReason(str, Enum):
    """Stable machine-readable coaching signals for future aggregation."""

    HANGING_PIECE = "hanging_piece"
    IMMEDIATE_CAPTURE = "immediate_capture"
    DOUBLE_ATTACK = "double_attack"
    SCORE_DEVIATION = "score_deviation"
    CAPTURE = "capture"
    CHECK = "check"


@dataclass(frozen=True)
class CoachingInsight:
    severity: CoachingSeverity
    message: str
    score_delta_cp: Optional[int]
    next_action: str
    reason_codes: tuple[CoachingReason, ...] = ()


ACCEPTABLE_DELTA_CP = -25
INACCURACY_DELTA_CP = -150

_PIECE_OBJECT_LABELS = {
    PieceType.GENERAL: "장군을",
    PieceType.CHARIOT: "차를",
    PieceType.CANNON: "포를",
    PieceType.HORSE: "마를",
    PieceType.ELEPHANT: "상을",
    PieceType.GUARD: "사를",
    PieceType.SOLDIER: "졸/병을",
}


def coach_move(analysis: MoveAnalysis) -> CoachingInsight:
    """Translate raw move analysis into conservative learner-facing feedback."""

    reason_codes = _reason_codes(analysis)

    if analysis.recommended_move is None or analysis.is_best_move is None:
        return CoachingInsight(
            severity=CoachingSeverity.UNAVAILABLE,
            message="현재 기준으로 비교할 엔진 추천수가 없습니다.",
            score_delta_cp=analysis.score_delta_cp,
            next_action="분석 가능한 추천수가 생긴 뒤 비교하세요.",
            reason_codes=(),
        )

    if analysis.is_best_move:
        next_action = _recommended_action(analysis)
        return CoachingInsight(
            severity=CoachingSeverity.RECOMMENDED,
            message=_feature_message(analysis, _recommended_base(analysis)),
            score_delta_cp=analysis.score_delta_cp,
            next_action=next_action,
            reason_codes=reason_codes,
        )

    delta = analysis.score_delta_cp
    if delta is None:
        return CoachingInsight(
            severity=CoachingSeverity.UNAVAILABLE,
            message="현재 기준으로 수의 평가 변화를 계산할 수 없습니다.",
            score_delta_cp=None,
            next_action="평가 변화가 계산되는 위치에서 다시 비교하세요.",
            reason_codes=reason_codes,
        )

    if analysis.tactical_risk is TacticalRisk.HANGING_PIECE:
        severity = CoachingSeverity.MAJOR_MISTAKE
        base = "핵심 문제는 전술 위험입니다. 이동한 기물이 바로 잡힐 수 있습니다. 다음에는 상대의 잡을 수 있는 수를 먼저 확인하고, 가능하면 이동한 기물을 보호하세요."
        next_action = "상대가 바로 잡을 수 있는 수와 기물 보호 수를 확인하세요."
    elif analysis.tactical_risk is TacticalRisk.IMMEDIATE_CAPTURE:
        severity = _score_severity(delta)
        base = "상대가 이동한 기물을 바로 잡을 수 있습니다. 교환을 의도한 수라면 상대의 잡기 뒤에 내가 되잡을 수 있는지까지 확인하세요."
        next_action = "상대가 잡은 뒤 내가 되잡을 수 있는지 확인하세요."
    else:
        severity = _score_severity(delta)
        if severity is CoachingSeverity.ACCEPTABLE:
            base = "추천수는 아니지만 괜찮은 대안입니다. 다음에는 추천수와 무엇이 다른지 한 번 비교해보세요."
            next_action = "추천수와 목적과 다음 진행이 어떻게 다른지 비교하세요."
        elif severity is CoachingSeverity.INACCURACY:
            base = "추천수보다 불리한 수입니다. 다음에는 같은 의도를 유지하면서 상대의 반격을 한 수 더 확인해보세요."
            next_action = "같은 의도를 유지하면서 상대의 다음 반격을 한 수 더 확인하세요."
        else:
            base = "현재 기준 평가가 크게 나빠지는 수입니다. 다음에는 눈앞의 이득보다 상대의 즉각적인 반격 가능성을 먼저 확인해보세요."
            next_action = "상대의 즉각적인 반격 수부터 찾아보세요."

    return CoachingInsight(
        severity=severity,
        message=_feature_message(analysis, base),
        score_delta_cp=delta,
        next_action=next_action,
        reason_codes=reason_codes,
    )


def _reason_codes(analysis: MoveAnalysis) -> tuple[CoachingReason, ...]:
    """Expose stable, composable analysis signals without parsing message text."""

    codes: list[CoachingReason] = []
    if analysis.tactical_risk is TacticalRisk.HANGING_PIECE:
        codes.append(CoachingReason.HANGING_PIECE)
    elif analysis.tactical_risk is TacticalRisk.IMMEDIATE_CAPTURE:
        codes.append(CoachingReason.IMMEDIATE_CAPTURE)
    if TacticalMotif.DOUBLE_ATTACK in analysis.tactical_motifs:
        codes.append(CoachingReason.DOUBLE_ATTACK)
    if analysis.captured_piece is not None:
        codes.append(CoachingReason.CAPTURE)
    if analysis.gives_check:
        codes.append(CoachingReason.CHECK)
    if analysis.is_best_move is False and analysis.score_delta_cp is not None:
        codes.append(CoachingReason.SCORE_DEVIATION)
    return tuple(codes)


def _score_severity(delta: int) -> CoachingSeverity:
    if delta >= ACCEPTABLE_DELTA_CP:
        return CoachingSeverity.ACCEPTABLE
    if delta >= INACCURACY_DELTA_CP:
        return CoachingSeverity.INACCURACY
    return CoachingSeverity.MAJOR_MISTAKE


def _recommended_action(analysis: MoveAnalysis) -> str:
    if analysis.captured_piece is not None:
        return "잡은 뒤 상대의 다음 반격을 확인하세요."
    if analysis.gives_check:
        return "상대가 선택할 수 있는 응수를 한 수 확인하세요."
    return "이 수를 둔 목적과 다음 진행을 이어서 확인하세요."


def _recommended_base(analysis: MoveAnalysis) -> str:
    if analysis.captured_piece is not None and analysis.gives_check:
        return "좋은 수입니다. 잡기와 장군을 동시에 만들어 상대에게 대응을 요구합니다."
    if analysis.captured_piece is not None:
        return "좋은 수입니다. 현재 기준 엔진 추천수와 같습니다. 잡은 뒤 상대의 다음 반격도 확인해보세요."
    if analysis.gives_check:
        return "좋은 수입니다. 현재 기준 엔진 추천수와 같고 장군으로 상대의 대응을 제한합니다."
    return "좋은 수입니다. 현재 기준 엔진 추천수와 같습니다."


def _feature_message(analysis: MoveAnalysis, base: str) -> str:
    features: list[str] = []
    if analysis.moved_piece is not None:
        features.append(f"{_PIECE_OBJECT_LABELS[analysis.moved_piece]} 이동했습니다")
    if analysis.captured_piece is not None:
        features.append(f"상대 {_PIECE_OBJECT_LABELS[analysis.captured_piece]} 잡았습니다")
    if analysis.gives_check:
        features.append("장군을 걸었습니다")
    if analysis.tactical_risk is TacticalRisk.HANGING_PIECE:
        features.append("이동한 기물이 걸려 있습니다")
    elif analysis.destination_attacked:
        features.append("이동한 칸을 상대가 바로 잡을 수 있습니다")
    if TacticalMotif.DOUBLE_ATTACK in analysis.tactical_motifs:
        features.append("상대가 다음 수에 두 기물을 동시에 공격할 수 있습니다")
    if not features:
        return base
    return f"{', '.join(features)}. {base}"
