"""
Small helper for loading JSON/YAML configuration files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None


def load_structured_file(path: Path) -> Mapping[str, object]:
    text = Path(path).read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text) or {}
    return json.loads(text or "{}")
