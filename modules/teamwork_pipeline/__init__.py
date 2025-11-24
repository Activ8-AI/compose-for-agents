"""
Teamwork pipeline package.

Exports the key surface area so the agent hub can wire the reflex execution
layer into Teamwork without leaking implementation details.
"""

from .client import TeamworkClientProtocol, TeamworkHTTPClient, TeamworkMemoryClient
from .logger import CustodianLogger
from .notifier import NullNotifier, SlackWebhookNotifier
from .pipeline import TeamworkPipeline
from .writer import CharterBriefWriter

__all__ = [
    "TeamworkPipeline",
    "CharterBriefWriter",
    "CustodianLogger",
    "TeamworkClientProtocol",
    "TeamworkHTTPClient",
    "TeamworkMemoryClient",
    "NullNotifier",
    "SlackWebhookNotifier",
]
