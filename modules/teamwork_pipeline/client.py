"""
Teamwork client abstractions.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, MutableMapping, Protocol, Sequence


class TeamworkClientProtocol(Protocol):
    def create_task(
        self,
        *,
        project_id: str,
        task_name: str,
        description: str,
        due: str | None = None,
        tags: Sequence[str] | None = None,
        assignee_id: str | None = None,
    ) -> str:  # pragma: no cover - protocol
        ...

    def create_subtask(
        self,
        *,
        parent_id: str,
        project_id: str,
        task_name: str,
        assignee_id: str | None = None,
    ) -> str:  # pragma: no cover - protocol
        ...

    def create_sprint(
        self,
        *,
        project_id: str,
        name: str,
        tasks: Sequence[str],
    ) -> str:  # pragma: no cover - protocol
        ...


class TeamworkHTTPClient:
    """
    Minimal HTTP client for the Teamwork Projects API.
    """

    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    def create_task(
        self,
        *,
        project_id: str,
        task_name: str,
        description: str,
        due: str | None = None,
        tags: Sequence[str] | None = None,
        assignee_id: str | None = None,
    ) -> str:
        payload = {
            "todo-item": {
                "content": task_name,
                "description": description,
                "projectId": project_id,
                "tags": ",".join(tags or []),
            }
        }
        if due:
            payload["todo-item"]["due-date"] = due.replace("-", "")
        if assignee_id:
            payload["todo-item"]["responsible-party-ids"] = assignee_id
        data = self._request("POST", "/tasks.json", payload)
        return str(data.get("id") or data.get("todo-item", {}).get("id"))

    def create_subtask(
        self,
        *,
        parent_id: str,
        project_id: str,
        task_name: str,
        assignee_id: str | None = None,
    ) -> str:
        payload = {
            "todo-item": {
                "content": task_name,
                "projectId": project_id,
                "parentTaskId": parent_id,
            }
        }
        if assignee_id:
            payload["todo-item"]["responsible-party-ids"] = assignee_id
        data = self._request("POST", "/tasks.json", payload)
        return str(data.get("id") or data.get("todo-item", {}).get("id"))

    def create_sprint(self, *, project_id: str, name: str, tasks: Sequence[str]) -> str:
        payload = {"sprint": {"name": name, "projectId": project_id, "taskIds": list(tasks)}}
        data = self._request("POST", "/sprints.json", payload)
        return str(data.get("id") or data.get("sprint", {}).get("id"))

    def _request(self, method: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=body, method=method)
        token = base64.b64encode(f"{self.api_token}:x".encode("utf-8")).decode("utf-8")
        request.add_header("Authorization", f"Basic {token}")
        request.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response_body = response.read().decode("utf-8")
                return json.loads(response_body or "{}")
        except urllib.error.URLError as exc:  # pragma: no cover - network paths
            raise RuntimeError("Teamwork API request failed") from exc

    @classmethod
    def from_environment(cls, *, optional: bool = True, fallback=None):
        base_url = os.getenv("TEAMWORK_BASE_URL")
        api_token = os.getenv("TEAMWORK_API_TOKEN")
        if base_url and api_token:
            return cls(base_url=base_url, api_token=api_token)
        if fallback is not None:
            return fallback
        if optional:
            return TeamworkMemoryClient()
        raise RuntimeError("Teamwork credentials missing")


class TeamworkMemoryClient:
    """
    Deterministic in-memory client useful for local dev and tests.
    """

    def __init__(self):
        self.tasks: MutableMapping[str, Dict[str, Any]] = {}
        self.sprints: MutableMapping[str, Dict[str, Any]] = {}
        self._counter = 0

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter}"

    def create_task(
        self,
        *,
        project_id: str,
        task_name: str,
        description: str,
        due: str | None = None,
        tags: Sequence[str] | None = None,
        assignee_id: str | None = None,
    ) -> str:
        task_id = self._next_id("task")
        self.tasks[task_id] = {
            "project_id": project_id,
            "task_name": task_name,
            "description": description,
            "due": due,
            "tags": list(tags or []),
            "assignee_id": assignee_id,
            "subtasks": [],
        }
        return task_id

    def create_subtask(
        self,
        *,
        parent_id: str,
        project_id: str,
        task_name: str,
        assignee_id: str | None = None,
    ) -> str:
        subtask_id = self._next_id("subtask")
        record = {
            "project_id": project_id,
            "task_name": task_name,
            "assignee_id": assignee_id,
            "parent_id": parent_id,
        }
        self.tasks.setdefault(parent_id, {}).setdefault("subtasks", []).append(record)
        self.tasks[subtask_id] = record
        return subtask_id

    def create_sprint(self, *, project_id: str, name: str, tasks: Sequence[str]) -> str:
        sprint_id = self._next_id("sprint")
        self.sprints[sprint_id] = {
            "project_id": project_id,
            "name": name,
            "tasks": list(tasks),
        }
        return sprint_id
