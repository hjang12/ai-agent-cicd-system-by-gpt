from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class ModelSpec:
    """Stable metadata describing an engine/model exposed to the application."""

    id: str
    display_name: str
    engine_name: str
    engine_version: Optional[str] = None
    rating: Optional[int] = None
    source: Optional[str] = None

    def __post_init__(self) -> None:
        for field_name in ("id", "display_name", "engine_name"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise ValueError(f"{field_name} must be a string")
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")

        if self.engine_version is not None and not isinstance(self.engine_version, str):
            raise ValueError("engine_version must be a string or null")
        if self.source is not None and not isinstance(self.source, str):
            raise ValueError("source must be a string or null")
        if self.rating is not None:
            if not isinstance(self.rating, int) or isinstance(self.rating, bool):
                raise ValueError("rating must be an integer or null")
            if self.rating < 0:
                raise ValueError("rating must be non-negative")


class ModelRegistry:
    """Small in-memory registry for validated model metadata.

    The registry deliberately stores metadata rather than engine instances. This
    keeps model selection independent from any concrete search or ML backend.
    """

    def __init__(self, models: Iterable[ModelSpec] = ()) -> None:
        self._models: dict[str, ModelSpec] = {}
        for model in models:
            self.register(model)

    def register(self, model: ModelSpec) -> ModelSpec:
        if not isinstance(model, ModelSpec):
            raise ValueError("model must be a ModelSpec")
        if model.id in self._models:
            raise ValueError(f"model id already registered: {model.id}")
        self._models[model.id] = model
        return model

    def get(self, model_id: str) -> ModelSpec:
        try:
            return self._models[model_id]
        except KeyError as exc:
            raise KeyError(f"unknown model id: {model_id}") from exc

    def maybe_get(self, model_id: str) -> Optional[ModelSpec]:
        return self._models.get(model_id)

    def list(self) -> tuple[ModelSpec, ...]:
        return tuple(self._models.values())

    def __len__(self) -> int:
        return len(self._models)

    def __contains__(self, model_id: str) -> bool:
        return model_id in self._models
