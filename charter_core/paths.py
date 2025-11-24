from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "logs"
EVIDENCE_DIR = REPO_ROOT / "evidence"
STATE_DIR = REPO_ROOT / "state"
DASHBOARD_DIR = REPO_ROOT / "dashboard"

for _path in (LOG_DIR, EVIDENCE_DIR, STATE_DIR, DASHBOARD_DIR):
    _path.mkdir(parents=True, exist_ok=True)

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
