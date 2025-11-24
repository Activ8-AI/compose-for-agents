"""
Core utilities for the Meta Mega Codex charter implementation.

This package centralizes paths, policy handling, evidence coordination,
and restart-safe helpers that are shared across the layered governors.
"""

from .paths import (
    REPO_ROOT,
    LOG_DIR,
    EVIDENCE_DIR,
    STATE_DIR,
    DASHBOARD_DIR,
    TIMESTAMP_FORMAT,
)

from .policies import load_policy_bundle
from .state import persist_state_snapshot, load_state_snapshot
from .governance import execute_governor

__all__ = [
    "REPO_ROOT",
    "LOG_DIR",
    "EVIDENCE_DIR",
    "STATE_DIR",
    "DASHBOARD_DIR",
    "TIMESTAMP_FORMAT",
    "load_policy_bundle",
    "persist_state_snapshot",
    "load_state_snapshot",
    "execute_governor",
]
