"""
Client matrix loader that maps MAOS client identifiers to Teamwork metadata.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    yaml = None


@dataclass(frozen=True, slots=True)
class ClientProfile:
    client_id: str
    teamwork_project_id: str
    display_name: str
    default_owner_id: Optional[str] = None
    primary_role_id: Optional[str] = None


class ClientMatrix:
    def __init__(self, clients: Mapping[str, ClientProfile]):
        self._clients = dict(clients)

    def resolve(self, client_id: str) -> Optional[ClientProfile]:
        return self._clients.get(client_id)

    @classmethod
    def from_file(cls, path: Path) -> "ClientMatrix":
        data = _load_structured_file(path)
        clients_section = data.get("clients", {})
        clients: Dict[str, ClientProfile] = {}
        for client_id, payload in clients_section.items():
            profile = ClientProfile(
                client_id=client_id,
                teamwork_project_id=str(payload["teamwork_project_id"]),
                display_name=payload.get("display_name", client_id),
                default_owner_id=payload.get("default_owner_id"),
                primary_role_id=payload.get("primary_role_id"),
            )
            clients[client_id] = profile
        return cls(clients)


def _load_structured_file(path: Path) -> Mapping[str, object]:
    text = Path(path).read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(text) or {}
    return json.loads(text or "{}")
