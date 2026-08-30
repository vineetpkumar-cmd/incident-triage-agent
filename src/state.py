from typing import Any, NotRequired, TypedDict


class IncidentState(TypedDict):
    """Data shared between LangGraph workflow nodes."""

    incident_number: str

    incident: NotRequired[dict[str, Any]]
    sla: NotRequired[dict[str, Any]]
    related_incidents: NotRequired[dict[str, Any]]
    jira_search: NotRequired[dict[str, Any]]

    decision: NotRequired[str]
    jira_action: NotRequired[str]
    email_subject: NotRequired[str]
    email_body: NotRequired[str]

    approved: NotRequired[bool]
    human_feedback: NotRequired[str]

    jira_result: NotRequired[dict[str, Any]]
    draft_result: NotRequired[dict[str, Any]]
    send_result: NotRequired[dict[str, Any]]

    stage: NotRequired[str]
    retry_count: NotRequired[int]
    error: NotRequired[str]