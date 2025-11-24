import unittest
from datetime import date

from client_matrix import ClientMatrix, ClientProfile
from modules.teamwork_pipeline import (
    CharterBriefWriter,
    NullNotifier,
    TeamworkMemoryClient,
    TeamworkPipeline,
)


class DummyLogger:
    def __init__(self):
        self.entries = []

    def audit(self, **payload):
        self.entries.append(payload)


class TeamworkPipelineTest(unittest.TestCase):
    def setUp(self):
        profile = ClientProfile(
            client_id="wilson_case",
            teamwork_project_id="2001001",
            display_name="Wilson Case",
            default_owner_id="owner-ops",
            primary_role_id="role:ops.wilson_case",
        )
        self.client_matrix = ClientMatrix({"wilson_case": profile})
        self.teamwork = TeamworkMemoryClient()
        self.logger = DummyLogger()
        self.pipeline = TeamworkPipeline(
            teamwork=self.teamwork,
            client_matrix=self.client_matrix,
            writer=CharterBriefWriter(["Fly Like an Eagle."]),
            logger=self.logger,
            notifier=NullNotifier(),
        )

    def test_dispatch_builds_full_task_stack(self):
        payload = {
            "client_id": "wilson_case",
            "reflex": "competitor_reflex",
            "urgency": 5,
            "title": "Competitor Price Change Detected",
            "description": "Competitor X adjusted pricing by 7%.",
            "actions": [
                "Run Pricing Impact Model",
                "Update Competitor Watch",
                "Generate Positioning Brief",
            ],
            "due_date": date(2025, 11, 2).isoformat(),
            "tags": ["competitor", "pricing"],
            "evidence_urls": ["https://example.com/source"],
            "source_event": "event_id:maos.competitor.signal:abc123",
            "confidence": 0.91,
        }

        result = self.pipeline.dispatch(payload)

        self.assertIn(result["task_id"], self.teamwork.tasks)
        task = self.teamwork.tasks[result["task_id"]]
        self.assertIn("competitor_reflex", task["tags"])
        self.assertEqual(len(task["subtasks"]), 3)
        self.assertTrue(self.teamwork.sprints)
        self.assertEqual(self.logger.entries[-1]["client_id"], "wilson_case")
        self.assertEqual(result["reflex"], "competitor_reflex")


if __name__ == "__main__":
    unittest.main()
