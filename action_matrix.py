"""
Action Matrix wiring to map reflexes onto execution pipelines.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, MutableMapping

from structured_file import load_structured_file


class ActionMatrix:
    def __init__(self, config_path: Path):
        config = load_structured_file(config_path)
        self.execution_pipeline_map: MutableMapping[str, str] = dict(
            config.get("execution_pipeline", {})
        )
        self._execution_pipeline = None

    def bind_execution_pipeline(self, pipeline) -> None:
        self._execution_pipeline = pipeline

    def handle(self, reflex_name: str, execution_intent) -> Mapping[str, object]:
        action = self.execution_pipeline_map.get(reflex_name)
        if action == "dispatch":
            if not self._execution_pipeline:
                raise RuntimeError("Execution pipeline not bound")
            return self._execution_pipeline.dispatch(execution_intent)
        raise KeyError(f"Reflex {reflex_name} is not mapped in the execution pipeline")
