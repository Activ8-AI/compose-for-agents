"""
Dataclasses shared across the Teamwork pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .exceptions import InvalidExecutionIntentError


def _ensure_list(value: Any, field_name: str) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value]
    raise InvalidExecutionIntentError(f"{field_name} must be a list of strings")


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    """
    Canonical representation of the reflex -> execution payload.
    """

    client_id: str
    reflex: str
    urgency: int
    title: str
    description: str
    actions: Sequence[str]
    due_date: Optional[date]
    tags: Sequence[str]
    evidence_urls: Sequence[str]
    source_event: str
    confidence: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ExecutionIntent":
        """Validate and normalize an arbitrary payload."""

        missing = [key for key in ("client_id", "reflex", "title") if key not in payload]
        if missing:
            raise InvalidExecutionIntentError(
                f"Execution intent missing required fields: {', '.join(missing)}"
            )

        actions = _ensure_list(payload.get("actions", []), "actions")
        if not actions:
            raise InvalidExecutionIntentError("Execution intent must include at least one action")

        tags = _ensure_list(payload.get("tags", []), "tags")
        evidence = _ensure_list(payload.get("evidence_urls", []), "evidence_urls")

        urgency = int(payload.get("urgency", 1))
        due_date_obj = cls._parse_due_date(payload.get("due_date"))
        confidence = float(payload.get("confidence", 0.0))

        return cls(
            client_id=str(payload["client_id"]),
            reflex=str(payload["reflex"]),
            urgency=urgency,
            title=str(payload["title"]),
            description=str(payload.get("description", "")).strip(),
            actions=tuple(actions),
            due_date=due_date_obj,
            tags=tuple(tags),
            evidence_urls=tuple(evidence),
            source_event=str(payload.get("source_event", "")),
            confidence=confidence,
            metadata=dict(payload.get("metadata", {})),
        )

    @staticmethod
    def _parse_due_date(value: Any) -> Optional[date]:
        if value in (None, ""):
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, (int, float)):
            return datetime.utcfromtimestamp(value).date()
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise InvalidExecutionIntentError(
                f"due_date must be ISO-8601 date, received {value!r}"
            ) from exc

    @property
    def due_date_iso(self) -> Optional[str]:
        return self.due_date.isoformat() if self.due_date else None

    @property
    def normalized_tags(self) -> Sequence[str]:
        unique = []
        seen = set()
        for tag in [*self.tags, "reflex", "auto", self.reflex]:
            needle = tag.strip().lower()
            if not needle or needle in seen:
                continue
            seen.add(needle)
            unique.append(needle)
        return tuple(unique)
