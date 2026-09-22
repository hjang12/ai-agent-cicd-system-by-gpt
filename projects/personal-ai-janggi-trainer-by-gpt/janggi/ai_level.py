from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .search import SearchConfig


class AILevel(Enum):
    BEGINNER = "1"
    EASY = "2"
    MEDIUM = "3"
    HARD = "4"
    ADVANCED = "5"
    EXPERT = "6"


@dataclass(frozen=True)
class AILevelSpec:
    level: AILevel
    name: str
    description: str
    config: SearchConfig


AI_LEVELS: tuple[AILevelSpec, ...] = (
    AILevelSpec(
        level=AILevel.BEGINNER,
        name="입문",
        description="즉시 응수하는 최소 탐색",
        config=SearchConfig(depth=1, mobility_weight=0, quiescence_depth=0, root_refinement_count=0),
    ),
    AILevelSpec(
        level=AILevel.EASY,
        name="초급",
        description="얕은 탐색 + 기본 활동성",
        config=SearchConfig(depth=1, mobility_weight=2, quiescence_depth=0, root_refinement_count=0),
    ),
    AILevelSpec(
        level=AILevel.MEDIUM,
        name="중급",
        description="2수 앞까지 기본 탐색",
        config=SearchConfig(depth=2, mobility_weight=2, quiescence_depth=0, root_refinement_count=0),
    ),
    AILevelSpec(
        level=AILevel.HARD,
        name="고급",
        description="2수 탐색 + 강제수 연장",
        config=SearchConfig(depth=2, mobility_weight=2, quiescence_depth=1, root_refinement_count=0),
    ),
    AILevelSpec(
        level=AILevel.ADVANCED,
        name="상급",
        description="2수 탐색 + 전술 연장 + 상위 후보 재검토",
        config=SearchConfig(depth=2, mobility_weight=2, quiescence_depth=1, root_refinement_count=2),
    ),
    AILevelSpec(
        level=AILevel.EXPERT,
        name="전문",
        description="3수 탐색 + 전술 연장",
        config=SearchConfig(depth=3, mobility_weight=2, quiescence_depth=1, root_refinement_count=0),
    ),
)


def get_ai_level(value: str | AILevel) -> AILevelSpec:
    if isinstance(value, AILevel):
        target = value
    elif isinstance(value, str):
        try:
            target = AILevel(value)
        except ValueError as exc:
            raise ValueError("ai_level must be one of 1, 2, 3, 4, 5, 6") from exc
    else:
        raise ValueError("ai_level must be a string from 1 to 6")

    for spec in AI_LEVELS:
        if spec.level is target:
            return spec
    raise ValueError("unknown ai level")


def ai_level_payload() -> list[dict[str, object]]:
    return [
        {
            "level": spec.level.value,
            "name": spec.name,
            "description": spec.description,
            "depth": spec.config.depth,
            "mobility_weight": spec.config.mobility_weight,
            "quiescence_depth": spec.config.quiescence_depth,
            "root_refinement_count": spec.config.root_refinement_count,
        }
        for spec in AI_LEVELS
    ]
