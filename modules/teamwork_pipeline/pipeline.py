"""
Reflex -> Teamwork execution pipeline.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Iterable, Mapping, Optional

from .client import TeamworkClientProtocol
from .exceptions import ClientNotFoundError
from .models import ExecutionIntent
from .notifier import NullNotifier, NotifierProtocol


class TeamworkPipeline:
    """
    Converts execution intents into fully structured Teamwork work items.
    """

    DEFAULT_SPRINT_REFLEXES = {
        "algorithm_reflex",
        "competitor_reflex",
        "market_reflex",
    }

    def __init__(
        self,
        *,
        teamwork: TeamworkClientProtocol,
        client_matrix,
        writer,
        logger,
        notifier: NotifierProtocol | None = None,
        sprint_reflexes: Optional[Iterable[str]] = None,
    ):
        self.teamwork = teamwork
        self.client_matrix = client_matrix
        self.writer = writer
        self.logger = logger
        self.notifier = notifier or NullNotifier()
        self.sprint_reflexes = set(sprint_reflexes or self.DEFAULT_SPRINT_REFLEXES)

    def dispatch(self, execution_intent: Mapping[str, Any] | ExecutionIntent) -> Mapping[str, Any]:
        intent = (
            execution_intent
            if isinstance(execution_intent, ExecutionIntent)
            else ExecutionIntent.from_payload(execution_intent)
        )

        profile = self.client_matrix.resolve(intent.client_id)
        if profile is None:
            raise ClientNotFoundError(f"Client {intent.client_id} is not in the matrix")

        description = self.writer.attach_brief(intent)
        task_id = self.teamwork.create_task(
            project_id=profile.teamwork_project_id,
            task_name=intent.title,
            description=description,
            due=intent.due_date_iso,
            tags=intent.normalized_tags,
            assignee_id=profile.default_owner_id,
        )

        for action in intent.actions:
            self.teamwork.create_subtask(
                parent_id=task_id,
                project_id=profile.teamwork_project_id,
                task_name=action,
                assignee_id=profile.default_owner_id,
            )

        sprint_id = None
        if self._should_create_sprint(intent):
            sprint_id = self.teamwork.create_sprint(
                project_id=profile.teamwork_project_id,
                name=self._compose_sprint_name(profile.display_name, intent),
                tasks=[task_id],
            )

        event_payload = {
            "client_id": intent.client_id,
            "project_id": profile.teamwork_project_id,
            "task_id": task_id,
            "sprint_id": sprint_id,
            "reflex": intent.reflex,
            "urgency": intent.urgency,
            "due_date": intent.due_date_iso,
            "source_event": intent.source_event,
            "confidence": intent.confidence,
        }
        self.logger.audit(**event_payload)

        if getattr(profile, "primary_role_id", None):
            message = f"{intent.title} - Task {task_id} due {intent.due_date_iso or 'TBD'}"
            self.notifier.notify(profile.primary_role_id, message, event_payload)

        return event_payload

    def _should_create_sprint(self, intent: ExecutionIntent) -> bool:
        return intent.urgency >= 4 and intent.reflex in self.sprint_reflexes

    @staticmethod
    def _compose_sprint_name(client_display_name: str, intent: ExecutionIntent) -> str:
        due_or_today = intent.due_date_iso or date.today().isoformat()
        return f"{client_display_name} - Reflex Window - {due_or_today}"
