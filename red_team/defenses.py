"""Transparent deterministic input and output guardrails."""

import re
from typing import Any, Literal, TypedDict


class GuardrailDecision(TypedDict):
    action: Literal["allow", "block", "review"]
    reasons: list[str]


INPUT_PATTERNS = {
    "instruction_override": re.compile(
        r"\b(ignore|disregard|override|bypass)\b.{0,50}\b(instructions?|rules?|approval|policy)\b",
        re.I,
    ),
    "internal_request": re.compile(
        r"\b(system prompt|hidden instruction|tool schema|chain of thought)\b", re.I
    ),
    "authority_claim": re.compile(
        r"\b(i am|i'm)\b.{0,30}\b(admin|executive|auditor|manager)\b", re.I
    ),
    "encoded_payload": re.compile(r"\b[A-Za-z0-9+/]{24,}={0,2}\b"),
}
OUTPUT_PATTERNS = {
    "internal_disclosure": re.compile(
        r"\b(system prompt|hidden instruction|tool schema|chain of thought|create_jira_issue)\b",
        re.I,
    ),
    "pii_disclosure": re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|\b\+?\d[\d\s-]{8,}\d\b",
        re.I,
    ),
}


def inspect_input(text: str) -> GuardrailDecision:
    """Classify a user request before workflow retrieval or tool use."""

    value = str(text or "")
    reasons = [name for name, pattern in INPUT_PATTERNS.items() if pattern.search(value)]
    if any(reason in {"instruction_override", "internal_request"} for reason in reasons):
        return {"action": "block", "reasons": reasons}
    if reasons:
        return {"action": "review", "reasons": reasons}
    return {"action": "allow", "reasons": []}


def inspect_output(text: str) -> GuardrailDecision:
    """Block customer-visible internal details or fictional PII patterns."""

    value = str(text or "")
    reasons = [name for name, pattern in OUTPUT_PATTERNS.items() if pattern.search(value)]
    if reasons:
        return {"action": "block", "reasons": reasons}
    return {"action": "allow", "reasons": []}


def _events(state: dict[str, Any], phase: str, decision: GuardrailDecision) -> list[dict[str, Any]]:
    return list(state.get("guardrail_events", [])) + [{
        "phase": phase,
        "action": decision["action"],
        "reasons": list(decision["reasons"]),
    }]


def input_guardrail_node(state: dict[str, Any]) -> dict[str, Any]:
    """Apply input inspection only when defended mode is enabled."""

    if not state.get("defense_mode", False):
        return {}
    decision = inspect_input(str(state.get("user_request", "")))
    result: dict[str, Any] = {"guardrail_events": _events(state, "input", decision)}
    if decision["action"] == "allow":
        return result
    result.update({
        "decision": "wait",
        "jira_action": "none",
        "stage": "input_blocked" if decision["action"] == "block" else "input_review",
        "visible_response": (
            "I can’t process that request automatically. It has been stopped for safe review."
        ),
    })
    return result


def output_guardrail_node(state: dict[str, Any]) -> dict[str, Any]:
    """Inspect the final user-visible text in defended mode."""

    if not state.get("defense_mode", False):
        return {}
    visible = str(state.get("visible_response") or state.get("email_body") or "")
    decision = inspect_output(visible)
    result: dict[str, Any] = {
        "guardrail_events": _events(state, "output", decision),
        "visible_response": visible,
    }
    if decision["action"] == "block":
        result.update({
            "stage": "output_blocked",
            "visible_response": "The response was withheld because it contained restricted information.",
        })
    return result
