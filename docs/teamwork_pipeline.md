# Teamwork Pipeline (MAOS Reflex -> Execution)

This document explains how the new reflex execution layer converts every
`ExecutionIntent` into real Teamwork work.

## Components

- `modules/teamwork_pipeline/` - production-ready pipeline, Teamwork client,
  charter brief writer, Custodian logger, and Slack notifier
- `client_matrix.py` - resolves `client_id -> teamwork_project_id` plus default
  owner/role ids
- `configs/action_matrix.yaml` - maps reflex names to the `dispatch` action
- `agent_hub.py` - wires the Action Matrix into the Teamwork pipeline and binds
  charter statements:  
  _Fly Like an Eagle. God is Good. God's Mercy Renews Every Morning. His Love
  Endures Forever._

## Execution Flow

```
EventBus
  -> Reflex DAG
       -> Execution Intent Payload
             -> Action Matrix (`execution_pipeline.dispatch`)
                   -> `TeamworkPipeline.dispatch(...)`
                         -> Teamwork task + subtasks (+ optional sprint)
                               -> Custodian Hub log + Slack RoleID ping
```

## Environment

Set `TEAMWORK_BASE_URL` and `TEAMWORK_API_TOKEN` to upgrade from the default
in-memory client to the real Teamwork REST API. Optionally set
`SLACK_WEBHOOK_URL` to mirror reflex dispatches into the client's primary RoleID
channel.

## Testing

Run `python -m unittest discover -s tests` to validate the dispatch path using
the deterministic in-memory Teamwork client.
