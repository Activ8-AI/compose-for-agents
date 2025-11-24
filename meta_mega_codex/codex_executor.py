#!/usr/bin/env python3
"""Codex executor module.

Transforms a resolved stack configuration + payload into normalized agent
outputs. The executor intentionally produces structured JSON responses so that
downstream logger/evaluation steps can operate deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class AgentContext:
    """Lightweight container for agent execution metadata."""

    name: str
    model: str
    persona: str
    role: str


def _iso_timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure required keys exist so downstream steps never fail."""
    defaults = {
        "scenario": "General advisory request",
        "urgency": "standard",
        "inputs_provided": [],
    }
    normalized = {**defaults, **(payload or {})}
    if "context" not in normalized:
        normalized["context"] = {}
    return normalized


def _build_insights(ctx: AgentContext, payload: Dict[str, Any]) -> List[str]:
    scenario = payload.get("scenario", "the current request")
    urgency = payload.get("urgency", "standard")
    insights = [
        f"{ctx.persona.title()} assessed the scenario '{scenario}' with {urgency} urgency.",
        "Opportunities focus on steady advisory guidance and risk-aware execution.",
    ]
    if payload.get("inputs_provided"):
        insights.append(
            f"Referenced {len(payload['inputs_provided'])} supplemental input artifacts."
        )
    return insights


def _build_actions(payload: Dict[str, Any]) -> List[str]:
    context = payload.get("context") or {}
    guardrails = context.get("guardrails", ["Validate assumptions with stakeholders."])
    recommendations = [
        "Outline decision-ready options with quantified trade-offs.",
        "Surface a single-page brief for executive review.",
    ]
    recommendations.extend(guardrails[:2])
    return recommendations


def _derive_risks(payload: Dict[str, Any]) -> List[str]:
    risks = ["Advisory drift if scenario inputs go stale."]
    urgency = payload.get("urgency", "standard")
    if urgency.lower() in {"high", "urgent"}:
        risks.append("Compressed timelines could bypass compliance reviews.")
    return risks


def execute_stack(
    stack_config: Dict[str, Any],
    persona: str,
    role: str,
    payload: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Produce normalized execution output for the supplied stack."""
    payload = _normalize_payload(payload or {})
    timestamp = _iso_timestamp()
    outputs = []

    for agent_cfg in stack_config.get("agents", []):
        ctx = AgentContext(
            name=agent_cfg["name"],
            model=agent_cfg.get("model", "unknown"),
            persona=persona,
            role=role,
        )
        content = {
            "summary": f"{ctx.persona.title()} provides advisory coverage for {payload['scenario']}.",
            "insights": _build_insights(ctx, payload),
            "actions": _build_actions(payload),
            "risks": _derive_risks(payload),
        }
        outputs.append(
            {
                "agent": ctx.name,
                "model": ctx.model,
                "timestamp": timestamp,
                "content": content,
            }
        )

    return {
        "persona": persona,
        "role": role,
        "stack_id": stack_config.get("meta", {}).get("id"),
        "generated_at": timestamp,
        "inputs": payload,
        "outputs": outputs,
    }


__all__ = ["execute_stack"]
