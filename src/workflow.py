from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from src.nodes import (
    assess_evidence,
    decide_action,
    enrich_incident,
    execute_jira_action,
    prepare_notification,
    retrieve_incident,
    search_jira,
    send_notification,
)
from src.state import IncidentState

def prepare_retrieval_retry(
    state: IncidentState,
) -> dict:
    """Clear old evidence before another retrieval attempt."""
    return {
        "retry_count": state.get("retry_count", 0) + 1,
        "incident": {},
        "sla": {},
        "related_incidents": {},
        "jira_search": {},
        "evidence_status": "pending",
        "missing_evidence": [],
        "error": None,
        "stage": "retrieval_retry_prepared",
    }


def route_after_evidence(
    state: IncidentState,
) -> str:
    """Continue, retry once, or request human help."""
    if state.get("evidence_status") == "sufficient":
        return "continue"

    if state.get("retry_count", 0) < 1:
        return "retry"

    return "human_review"


def retrieval_human_review(
    state: IncidentState,
) -> dict:
    """Pause when evidence remains incomplete."""
    response = interrupt(
        {
            "review_type": "retrieval",
            "message": (
                "Retrieval remains incomplete after one retry."
            ),
            "incident_number": state["incident_number"],
            "missing_evidence": state.get(
                "missing_evidence",
                [],
            ),
            "error": state.get("error"),
            "allowed_actions": ["retry", "stop"],
        }
    )

    if isinstance(response, dict):
        retry = bool(response.get("retry", False))
        feedback = str(response.get("feedback", ""))
    else:
        retry = False
        feedback = ""

    return {
        "retrieval_review_action": (
            "retry"
            if retry
            else "stop"
        ),
        "retrieval_feedback": feedback,
        "stage": (
            "retrieval_retry_requested"
            if retry
            else "retrieval_stopped"
        ),
    }

def route_after_retrieval_review(
    state: IncidentState,
) -> str:
    """Route according to the human's retrieval decision."""
    if state.get("retrieval_review_action") == "retry":
        return "retry"

    return "stop"





def route_after_retrieval(
    state: IncidentState,
) -> str:
    """Continue retrieval or assess a failed result."""
    if state.get("error"):
        return "assess"

    return "continue"


def human_approval(
    state: IncidentState,
) -> dict:
    """Pause P1/P2 incidents for human approval."""
    priority = state["incident"]["priority"]

    if priority not in {"P1", "P2"}:
        return {
            "approved": True,
            "stage": "automatically_approved",
        }

    response = interrupt(
        {
            "message": (
                f"Approve {priority} incident actions?"
            ),
            "incident": state["incident"],
            "jira_action": state["jira_action"],
            "email_subject": state["email_subject"],
            "email_body": state["email_body"],
        }
    )

    if isinstance(response, dict):
        approved = bool(
            response.get("approved", False)
        )
        feedback = str(
            response.get("feedback", "")
        )
    else:
        approved = bool(response)
        feedback = ""

    return {
        "approved": approved,
        "human_feedback": feedback,
        "stage": (
            "approved"
            if approved
            else "rejected"
        ),
    }



def route_after_decision(
    state: IncidentState,
) -> str:
    """Stop low-priority incidents that require no action."""
    if state["decision"] == "wait":
        return "stop"

    return "prepare"


def route_after_approval(
    state: IncidentState,
) -> str:
    """Only execute changes after approval."""
    if state.get("approved", False):
        return "execute"

    return "stop"


def build_workflow():
    """Build and compile the incident triage graph."""
    builder = StateGraph(IncidentState)

    builder.add_node(
        "retrieve_incident",
        retrieve_incident,
    )
    builder.add_node(
        "enrich_incident",
        enrich_incident,
    )
    builder.add_node(
        "search_jira",
        search_jira,
    )
    builder.add_node(
        "assess_evidence",
        assess_evidence,
    )
    builder.add_node(
        "prepare_retrieval_retry",
        prepare_retrieval_retry,
    )
    builder.add_node(
        "retrieval_human_review",
        retrieval_human_review,
    )


    builder.add_node(
        "decide_action",
        decide_action,
    )
    builder.add_node(
        "prepare_notification",
        prepare_notification,
    )
    builder.add_node(
        "human_approval",
        human_approval,
    )
    builder.add_node(
        "execute_jira_action",
        execute_jira_action,
    )
    builder.add_node(
        "send_notification",
        send_notification,
    )

    builder.add_edge(
        START,
        "retrieve_incident",
    )

    builder.add_conditional_edges(
        "retrieve_incident",
        route_after_retrieval,
        {
            "continue": "enrich_incident",
            "assess": "assess_evidence",
        },
    )
    

    builder.add_edge(
        "enrich_incident",
        "search_jira",
    )
    builder.add_edge(
        "search_jira",
        "assess_evidence",
    )
    builder.add_conditional_edges(
        "assess_evidence",
        route_after_evidence,
        {
            "continue": "decide_action",
            "retry": "prepare_retrieval_retry",
            "human_review": "retrieval_human_review",
        },
    )

    builder.add_edge(
        "prepare_retrieval_retry",
        "retrieve_incident",
    )
    builder.add_conditional_edges(
        "retrieval_human_review",
        route_after_retrieval_review,
        {
            "retry": "prepare_retrieval_retry",
            "stop": END,
        },
    )
    builder.add_conditional_edges(
        "decide_action",
        route_after_decision,
        {
            "prepare": "prepare_notification",
            "stop": END,
        },
    )

    builder.add_edge(
        "prepare_notification",
        "human_approval",
    )

    builder.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "execute": "execute_jira_action",
            "stop": END,
        },
    )

    builder.add_edge(
        "execute_jira_action",
        "send_notification",
    )
    builder.add_edge(
        "send_notification",
        END,
    )

    checkpointer = InMemorySaver()

    return builder.compile(
        checkpointer=checkpointer,
    )


workflow = build_workflow()