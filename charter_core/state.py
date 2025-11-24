from __future__ import annotations

import json
from typing import Dict, Any

from .paths import STATE_DIR

STATE_FILE = STATE_DIR / "governor_state.json"


def load_state_snapshot() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {"governors": {}}
    with STATE_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def persist_state_snapshot(payload: Dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = STATE_FILE.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    tmp_path.replace(STATE_FILE)
