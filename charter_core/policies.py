from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Any

from .paths import REPO_ROOT


POLICY_FILES = {
    "activ8": {
        "domain": "activ8_domain_policy.json",
        "copilot": "activ8-ai-copilot.json",
    },
    "lma": {
        "domain": "lma_domain_policy.json",
        "copilot": "lma-copilot.json",
    },
    "personal": {
        "domain": "personal_domain_policy.json",
        "copilot": "personal-copilot.json",
    },
}


@dataclass(frozen=True)
class PolicyBundle:
    governor: str
    domain_policy: Dict[str, Any]
    copilot_policy: Dict[str, Any]

    @property
    def version(self) -> str:
        return f"{self.domain_policy.get('version')}+{self.copilot_policy.get('version')}"


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_policy_bundle(governor: str) -> PolicyBundle:
    normalized = governor.lower()
    if normalized not in POLICY_FILES:
        raise ValueError(f"Unknown governor '{governor}'. Expected one of {sorted(POLICY_FILES)}.")

    files = POLICY_FILES[normalized]
    domain_path = REPO_ROOT / files["domain"]
    copilot_path = REPO_ROOT / files["copilot"]

    if not domain_path.exists():
        raise FileNotFoundError(f"Missing domain policy for '{governor}' at {domain_path}.")
    if not copilot_path.exists():
        raise FileNotFoundError(f"Missing copilot policy for '{governor}' at {copilot_path}.")

    return PolicyBundle(
        governor=normalized,
        domain_policy=_read_json(domain_path),
        copilot_policy=_read_json(copilot_path),
    )
