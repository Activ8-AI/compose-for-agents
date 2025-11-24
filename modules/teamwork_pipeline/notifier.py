"""
Notification plumbing for reflex dispatches.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Mapping, Protocol


class NotifierProtocol(Protocol):
    def notify(self, role_id: str, message: str, payload: Mapping[str, Any]) -> None:  # pragma: no cover - protocol
        ...


class NullNotifier:
    """Default no-op notifier."""

    def notify(self, role_id: str, message: str, payload: Mapping[str, Any]) -> None:
        return None


class SlackWebhookNotifier:
    """
    Minimal Slack notifier that posts JSON payloads to an incoming webhook.
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def notify(self, role_id: str, message: str, payload: Mapping[str, Any]) -> None:
        body = {
            "text": message,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Teamwork Dispatch* for `{role_id}`\n{message}",
                    },
                }
            ],
            "metadata": {"event_type": "teamwork_pipeline_dispatch", "event_payload": dict(payload)},
        }
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(self.webhook_url, data=data, method="POST")
        request.add_header("Content-Type", "application/json")

        try:
            urllib.request.urlopen(request, timeout=10)
        except urllib.error.URLError as exc:  # pragma: no cover - network paths
            raise RuntimeError("Failed to notify Slack") from exc

    @classmethod
    def from_environment(cls, optional: bool = True):
        url = os.getenv("SLACK_WEBHOOK_URL")
        if not url:
            if optional:
                return NullNotifier()
            raise RuntimeError("Missing SLACK_WEBHOOK_URL")
        return cls(url)
