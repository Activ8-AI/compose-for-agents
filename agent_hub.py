"""
MAOS agent hub wiring reflexes into the Teamwork execution pipeline.
"""

from __future__ import annotations

from pathlib import Path

from action_matrix import ActionMatrix
from client_matrix import ClientMatrix
from modules.teamwork_pipeline import (
    CharterBriefWriter,
    CustodianLogger,
    SlackWebhookNotifier,
    TeamworkHTTPClient,
    TeamworkMemoryClient,
    TeamworkPipeline,
)

CONFIG_DIR = Path(__file__).parent / "configs"

CLIENT_MATRIX = ClientMatrix.from_file(CONFIG_DIR / "clients.yaml")
ACTION_MATRIX = ActionMatrix(CONFIG_DIR / "action_matrix.yaml")
WRITER_AGENT = CharterBriefWriter(
    [
        "Fly Like an Eagle.",
        "God is Good.",
        "God's Mercy Renews Every Morning.",
        "His Love Endures Forever.",
    ]
)
CUSTODIAN_LOGGER = CustodianLogger(log_path=Path("logs/custodian_hub.log"))
TEAMWORK_CLIENT = TeamworkHTTPClient.from_environment(fallback=TeamworkMemoryClient())
NOTIFIER = SlackWebhookNotifier.from_environment(optional=True)

TEAMWORK_PIPELINE = TeamworkPipeline(
    teamwork=TEAMWORK_CLIENT,
    client_matrix=CLIENT_MATRIX,
    writer=WRITER_AGENT,
    logger=CUSTODIAN_LOGGER,
    notifier=NOTIFIER,
)

ACTION_MATRIX.bind_execution_pipeline(TEAMWORK_PIPELINE)

__all__ = ["ACTION_MATRIX", "TEAMWORK_PIPELINE"]
