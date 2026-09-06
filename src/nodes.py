import json
from typing import Any

from src.llm import generate_email_body
from src.mcp_client import get_mcp_tools
from src.state import IncidentState
from evaluation.telemetry import record_tool_call


_TOOL_CACHE: dict[str, Any] | None = None


async def get_tool(tool_name: str):
    """Return one LangChain-compatible MCP tool."""
    global _TOOL_CACHE

    if _TOOL_CACHE is None:
        tools = await get_mcp_tools()
        _TOOL_CACHE = {
            tool.name: tool
            for tool in tools
        }

    return _TOOL_CACHE[tool_name]


def normalize_result(result: Any) -> dict:
    """Convert an MCP tool result into a dictionary."""
    if isinstance(result, dict):
        return result

    if isinstance(result, str):
        return json.loads(result)

    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict) and "text" in item:
                return json.loads(item["text"])

    raise ValueError(
        f"Unsupported MCP result type: {type(result)}"
    )


async def call_tool(
    tool_name: str,
    arguments: dict,
) -> dict:
    """Invoke an MCP tool and normalize its response."""
    tool = await get_tool(tool_name)
    record_tool_call(tool_name)
    result = await tool.ainvoke(arguments)
    return normalize_result(result)


async def retrieve_incident(
    state: IncidentState,
) -> dict:
    """Retrieve the primary ServiceNow incident safely."""
    try:
        incident = await call_tool(
            "get_incident",
            {
                "incident_number": state["incident_number"],
            },
        )
    except Exception as error:
        return {
            "incident": {},
            "stage": "incident_retrieval_failed",
            "error": (
                "get_incident failed: "
                f"{type(error).__name__}"
            ),
        }

    if "error" in incident:
        return {
            "incident": {},
            "stage": "incident_retrieval_failed",
            "error": str(incident["error"]),
        }

    return {
        "incident": incident,
        "stage": "incident_retrieved",
        "error": None,
    }

async def enrich_incident(
    state: IncidentState,
) -> dict:
    """Retrieve SLA and related incidents safely."""
    incident_number = state["incident_number"]
    errors: list[str] = []

    try:
        sla = await call_tool(
            "get_incident_sla",
            {"incident_number": incident_number},
        )
    except Exception as error:
        sla = {}
        errors.append(
            "get_incident_sla failed: "
            f"{type(error).__name__}"
        )

    try:
        related = await call_tool(
            "search_related_incidents",
            {"incident_number": incident_number},
        )
    except Exception as error:
        related = {}
        errors.append(
            "search_related_incidents failed: "
            f"{type(error).__name__}"
        )

    return {
        "sla": sla,
        "related_incidents": related,
        "error": "; ".join(errors) if errors else None,
        "stage": (
            "incident_enrichment_failed"
            if errors
            else "incident_enriched"
        ),
    }

async def search_jira(
    state: IncidentState,
) -> dict:
    """Search Jira safely for an existing linked issue."""
    try:
        jira_search = await call_tool(
            "search_jira_issues",
            {
                "incident_number": state[
                    "incident_number"
                ],
            },
        )
    except Exception as error:
        return {
            "jira_search": {},
            "error": (
                "search_jira_issues failed: "
                f"{type(error).__name__}"
            ),
            "stage": "jira_search_failed",
        }

    if "error" in jira_search:
        return {
            "jira_search": {},
            "error": str(jira_search["error"]),
            "stage": "jira_search_failed",
        }

    return {
        "jira_search": jira_search,
        "stage": "jira_searched",
    }
async def assess_evidence(
    state: IncidentState,
) -> dict:
    """Check whether retrieved evidence is complete and valid."""
    missing: list[str] = []

    incident = state.get("incident")
    incident_fields = {
        "number",
        "short_description",
        "description",
        "priority",
        "state",
        "assignment_group",
        "engineering_required",
    }

    if not isinstance(incident, dict):
        missing.append("incident")
    else:
        for field in sorted(incident_fields):
            if field not in incident:
                missing.append(f"incident.{field}")

    sla = state.get("sla")

    if not isinstance(sla, dict):
        missing.append("sla")
    elif "sla_breached" not in sla:
        missing.append("sla.sla_breached")

    related = state.get("related_incidents")

    if not isinstance(related, dict):
        missing.append("related_incidents")
    else:
        if not isinstance(
            related.get("related_incidents"),
            list,
        ):
            missing.append(
                "related_incidents.related_incidents"
            )

        if not isinstance(related.get("total"), int):
            missing.append("related_incidents.total")

    jira_search = state.get("jira_search")

    if not isinstance(jira_search, dict):
        missing.append("jira_search")
    else:
        if not isinstance(jira_search.get("issues"), list):
            missing.append("jira_search.issues")

        if not isinstance(jira_search.get("total"), int):
            missing.append("jira_search.total")

    return {
        "evidence_status": (
            "sufficient"
            if not missing
            else "insufficient"
        ),
        "missing_evidence": missing,
        "stage": "evidence_assessed",
    }

async def decide_action(
    state: IncidentState,
) -> dict:
    """Choose whether to wait, notify, or escalate."""
    incident = state["incident"]
    sla = state["sla"]
    jira_search = state["jira_search"]

    priority = incident["priority"]
    sla_breached = sla["sla_breached"]

    if priority in {"P1", "P2"} or sla_breached:
        decision = "escalate"
    elif priority == "P3":
        decision = "notify"
    else:
        decision = "wait"

    if not incident["engineering_required"]:
        jira_action = "none"
    elif jira_search["total"] > 0:
        jira_action = "update"
    else:
        jira_action = "create"

    return {
        "decision": decision,
        "jira_action": jira_action,
        "stage": "decision_complete",
    }


async def prepare_notification(
    state: IncidentState,
) -> dict:
    """Prepare and store an Outlook email draft."""
    incident = state["incident"]
    jira_search = state["jira_search"]

    jira_text = "No Jira issue currently exists."

    if jira_search["total"] > 0:
        jira_key = jira_search["issues"][0]["key"]
        jira_text = f"Existing Jira issue: {jira_key}."

    subject = (
        f"{incident['priority']} incident "
        f"{incident['number']}: "
        f"{incident['short_description']}"
    )

    fallback_body = (
        f"Incident: {incident['number']}\n"
        f"Priority: {incident['priority']}\n"
        f"Description: {incident['description']}\n"
        f"Assignment group: "
        f"{incident['assignment_group']}\n"
        f"Decision: {state['decision']}\n"
        f"{jira_text}"
    )

    draft_source = "ollama"
    model_error = None

    try:
        body = await generate_email_body(
            incident=incident,
            decision=state["decision"],
            jira_text=jira_text,
        )
    except Exception as error:
        body = fallback_body
        draft_source = "template_fallback"
        model_error = type(error).__name__

    draft_result = await call_tool(
        "create_email_draft",
        {
            "recipients": [
                "incident-management@example.com"
            ],
            "subject": subject,
            "body": body,
            "incident_number": incident["number"],
        },
    )

    return {
        "email_subject": subject,
        "email_body": body,
        "draft_source": draft_source,
        "model_error": model_error,
        "draft_result": draft_result,
        "stage": "notification_drafted",
    }


async def execute_jira_action(
    state: IncidentState,
) -> dict:
    """Create or update the relevant Jira issue."""
    incident = state["incident"]
    jira_action = state["jira_action"]

    if jira_action == "none":
        return {
            "jira_result": {
                "status": "not_required",
            },
            "stage": "jira_complete",
        }

    if jira_action == "update":
        jira_key = state["jira_search"]["issues"][0][
            "key"
        ]

        result = await call_tool(
            "add_jira_comment",
            {
                "issue_key": jira_key,
                "comment": (
                    f"Update from {incident['number']}: "
                    f"{incident['description']}"
                ),
                "incident_priority": incident["priority"],
                "approved": state.get("approved", False),
            },
        )
    else:
        jira_priority = {
            "P1": "Highest",
            "P2": "High",
            "P3": "Medium",
            "P4": "Low",
        }.get(incident["priority"], "Medium")

        result = await call_tool(
            "create_jira_issue",
            {
                "project": "ENG",
                "issue_type": "Story",
                "summary": (
                    f"Investigate {incident['number']}: "
                    f"{incident['short_description']}"
                ),
                "description": incident["description"],
                "jira_priority": jira_priority,
                "linked_incident": incident["number"],
                "incident_priority": incident["priority"],
                "approved": state.get("approved", False),
            },
        )

    return {
        "jira_result": result,
        "stage": "jira_complete",
    }


async def send_notification(
    state: IncidentState,
) -> dict:
    """Send the approved Outlook draft."""
    draft_result = state["draft_result"]

    result = await call_tool(
        "send_email",
        {
            "draft_id": draft_result["draft"]["id"],
            "incident_priority": state["incident"][
                "priority"
            ],
            "approved": state.get("approved", False),
        },
    )

    return {
        "send_result": result,
        "stage": "complete",
    }
