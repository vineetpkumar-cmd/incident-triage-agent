"""Deterministic authorization for Incident Triage Agent tool calls."""

from typing import Any, TypedDict


class AuthorizationDecision(TypedDict):
    allowed: bool
    reasons: list[str]


READ_TOOLS = {
    "get_incident",
    "get_incident_sla",
    "search_related_incidents",
    "search_jira_issues",
}
WRITE_STAGES = {
    "create_email_draft": {"decision_complete"},
    "create_jira_issue": {"approved", "automatically_approved"},
    "add_jira_comment": {"approved", "automatically_approved"},
    "send_email": {"jira_complete"},
}
ALLOWED_RECIPIENTS = {"incident-management@example.com"}


def authorize_tool_call(
    tool_name: str, arguments: dict[str, Any], state: dict[str, Any]
) -> AuthorizationDecision:
    """Return an auditable allow/deny decision without invoking an LLM."""

    if tool_name not in READ_TOOLS | set(WRITE_STAGES):
        return {"allowed": False, "reasons": ["tool_not_allowed"]}

    reasons: list[str] = []
    active_incident = str(state.get("incident_number") or state.get("incident", {}).get("number") or "")
    scoped_values = [
        str(arguments[key])
        for key in ("incident_number", "linked_incident")
        if arguments.get(key) is not None
    ]
    if any(value != active_incident for value in scoped_values):
        reasons.append("incident_scope_mismatch")

    if tool_name in WRITE_STAGES:
        if state.get("stage") not in WRITE_STAGES[tool_name]:
            reasons.append("stage_not_allowed")

        priority = state.get("incident", {}).get("priority")
        if (
            tool_name in {"create_jira_issue", "add_jira_comment", "send_email"}
            and priority in {"P1", "P2"}
            and state.get("approved") is not True
        ):
            reasons.append("approval_required")

    if tool_name == "create_email_draft":
        recipients = set(arguments.get("recipients") or [])
        if not recipients or not recipients <= ALLOWED_RECIPIENTS:
            reasons.append("recipient_not_allowed")

    return {"allowed": not reasons, "reasons": reasons}
