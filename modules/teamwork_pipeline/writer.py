"""
Writers that turn execution intents into human-scannable briefs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from textwrap import indent
from typing import Iterable, Sequence

from .models import ExecutionIntent


class CharterBriefWriter:
    """
    Composes the charter-standard brief that gets attached to each Teamwork task.
    """

    def __init__(self, charter_statements: Sequence[str]):
        self.charter_statements = tuple(charter_statements)

    def attach_brief(self, intent: ExecutionIntent) -> str:
        charter_block = "\n".join(f"- {line}" for line in self.charter_statements)
        actions_block = "\n".join(f"- {action}" for action in intent.actions)
        evidence_block = (
            "\n".join(f"- {url}" for url in intent.evidence_urls) or "- No evidence links supplied"
        )

        generated_at = datetime.now(timezone.utc).isoformat()
        sections = [
            f"## Charter Alignment\n{charter_block}",
            f"## Reflex Synopsis\nReflex: **{intent.reflex}**\nUrgency: {intent.urgency}\nConfidence: {intent.confidence:.2f}",
            "## Description",
            indent(intent.description or "No description provided.", "  "),
            "## Actions",
            indent(actions_block, "  "),
            "## Evidence",
            indent(evidence_block, "  "),
            f"_Generated at {generated_at}_",
        ]

        return "\n\n".join(sections)
