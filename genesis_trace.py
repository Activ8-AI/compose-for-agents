from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from charter_core.paths import LOG_DIR, TIMESTAMP_FORMAT


@dataclass
class GenesisTracer:
    """Low-level trace log for deterministic replay."""

    trace_path: Path = field(default_factory=lambda: LOG_DIR / "genesis_trace.log")

    def trace(self, governor: str, event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        enriched = {
            "timestamp_utc": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
            "governor": governor,
            "event": event,
            "payload": payload,
        }
        line = json.dumps(enriched, sort_keys=True)
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        with self.trace_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return enriched
