from typing import Any, NotRequired, TypedDict


class IncidentState(TypedDict):
    """Data shared between LangGraph workflow nodes."""

    incident_number: str

    incident: NotRequired[dict[str, Any]]
    sla: NotRequired[dict[str, Any]]
    related_incidents: NotRequired[dict[str, Any]]
    jira_search: NotRequired[dict[str, Any]]
    evidence_status: NotRequired[str]
    missing_evidence: NotRequired[list[str]]
    retrieval_review_action: NotRequired[str]
    retrieval_feedback: NotRequired[str]

    decision: NotRequired[str]
    jira_action: NotRequired[str]
    email_subject: NotRequired[str]
    email_body: NotRequired[str]
    draft_source: NotRequired[str]
    model_error: NotRequired[str | None]

    approved: NotRequired[bool]
    human_feedback: NotRequired[str]

    jira_result: NotRequired[dict[str, Any]]
    draft_result: NotRequired[dict[str, Any]]
    send_result: NotRequired[dict[str, Any]]

    stage: NotRequired[str]
    retry_count: NotRequired[int]
    error: NotRequired[str| None]
