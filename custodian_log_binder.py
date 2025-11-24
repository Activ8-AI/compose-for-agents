from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from charter_core.paths import LOG_DIR, TIMESTAMP_FORMAT


@dataclass
class CustodianLogBinder:
    """Append-only custodian log that enforces immutable audit entries."""

    log_path: Path = field(default_factory=lambda: LOG_DIR / "custodian.log")

    def append(self, governor: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        enriched = {
            "timestamp_utc": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
            "governor": governor,
            **entry,
        }
        line = json.dumps(enriched, sort_keys=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return enriched
