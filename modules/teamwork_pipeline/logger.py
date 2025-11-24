"""
Custodian Hub logging helpers.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, MutableMapping


class CustodianLogger:
    """
    Emits SRR-complete audit events to the Custodian Hub log.
    """

    def __init__(self, log_path: Path):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def audit(self, **payload: Any) -> None:
        entry: MutableMapping[str, Any] = dict(payload)
        entry.setdefault("event", "teamwork_pipeline_dispatch")
        serialized = json.dumps(entry, sort_keys=True)
        entry["content_hash"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
