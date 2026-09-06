import asyncio
import re
import uuid

import streamlit as st
from langgraph.types import Command
from src.review import (
    build_review_response,
    is_retrieval_review,
)

from src.workflow import workflow


st.set_page_config(
    page_title="Incident Triage Agent",
    page_icon="🚨",
    layout="wide",
)


def run_workflow(value, config):
    """Run or resume the asynchronous LangGraph workflow."""
    return asyncio.run(
        workflow.ainvoke(
            value,
            config=config,
        )
    )


def reset_application() -> None:
    """Remove the current workflow from Streamlit state."""
    keys_to_remove = [
        "workflow_result",
        "workflow_config",
        "incident_number",
    ]

    for key in keys_to_remove:
        st.session_state.pop(key, None)


def display_workflow_state(result: dict) -> None:
    """Display the useful parts of the workflow state."""
    incident = result.get("incident")

    if incident:
        st.subheader("ServiceNow Incident")

        column1, column2, column3 = st.columns(3)

        column1.metric(
            "Incident",
            incident["number"],
        )
        column2.metric(
            "Priority",
            incident["priority"],
        )
        column3.metric(
            "State",
            incident["state"],
        )

        st.write(
            f"**Description:** "
            f"{incident['description']}"
        )
        st.write(
            f"**Assignment group:** "
            f"{incident['assignment_group']}"
        )

    evidence_status = result.get("evidence_status")

    if evidence_status:
        st.subheader("Retrieval Evidence")

        evidence_column, retry_column = st.columns(2)

        evidence_column.metric(
            "Evidence status",
            evidence_status.title(),
        )
        retry_column.metric(
            "Automatic retries",
            result.get("retry_count", 0),
        )

        missing = result.get("missing_evidence", [])

        if missing:
            st.warning(
                "Missing evidence: "
                + ", ".join(missing)
            )

    if result.get("decision"):
        st.subheader("Triage Decision")

        decision_column, jira_column = st.columns(2)

        decision_column.metric(
            "Decision",
            result["decision"].title(),
        )
        jira_column.metric(
            "Jira action",
            result.get(
                "jira_action",
                "none",
            ).title(),
        )

    related = result.get("related_incidents")

    if related:
        with st.expander("Related ServiceNow incidents"):
            st.json(related)

    jira_search = result.get("jira_search")

    if jira_search:
        with st.expander("Existing Jira search"):
            st.json(jira_search)

    if result.get("email_subject"):
        st.subheader("Outlook Draft")
        st.write(
            "**Draft source:** "
            f"{result.get('draft_source', 'unknown')}"
        )

        st.write(
            f"**Subject:** {result['email_subject']}"
        )
        st.text_area(
            "Draft body",
            value=result.get("email_body", ""),
            height=220,
            disabled=True,
        )

    if result.get("jira_result"):
        st.subheader("Jira Result")
        st.json(result["jira_result"])

    if result.get("send_result"):
        st.subheader("Outlook Send Result")
        st.json(result["send_result"])

    if result.get("error"):
        st.error(result["error"])


st.title("Incident Triage Agent")
st.caption(
    "LangGraph + LangChain MCP + Ollama + "
    "Mock ServiceNow, Jira and Outlook"
)

with st.sidebar:
    st.header("About")

    st.write(
        "This fictional learning application retrieves "
        "an incident, checks its SLA, coordinates Jira, "
        "drafts an Outlook notification, and pauses for "
        "human approval."
    )

    st.info(
        "P1 and P2 actions always require approval."
    )

    if st.button("Reset application"):
        reset_application()
        st.rerun()


incident_number = st.text_input(
    "ServiceNow incident number",
    placeholder="INC0010002",
).strip().upper()


if st.button(
    "Start Triage",
    type="primary",
    disabled=not incident_number,
):
    if not re.fullmatch(r"INC\d{7}", incident_number):
        st.error(
            "Enter INC followed by seven digits, "
            "for example INC0010002."
        )
    else:
        config = {
            "configurable": {
                "thread_id": str(uuid.uuid4()),
            }
        }

        initial_state = {
            "incident_number": incident_number,
            "stage": "started",
            "retry_count": 0,
        }

        try:
            with st.spinner(
                "Running triage and drafting notification..."
            ):
                result = run_workflow(
                    initial_state,
                    config,
                )

            st.session_state["workflow_result"] = result
            st.session_state["workflow_config"] = config
            st.session_state[
                "incident_number"
            ] = incident_number

        except Exception as error:
            st.exception(error)


result = st.session_state.get("workflow_result")

if result:
    display_workflow_state(result)

    interrupts = result.get("__interrupt__", [])

    if interrupts:
        approval_request = interrupts[0].value
        retrieval_review = is_retrieval_review(
            approval_request
        )

        accept_label = (
            "Retry retrieval"
            if retrieval_review
            else "Approve"
        )

        reject_label = (
            "Stop"
            if retrieval_review
            else "Reject"
        )
        st.warning("Human approval required")

        with st.expander(
            "Review approval request",
            expanded=True,
        ):
            st.json(approval_request)

        feedback = st.text_input(
            "Optional approval feedback"
        )

        approve_column, reject_column = st.columns(2)

        if approve_column.button(
            accept_label,
            type="primary",
            use_container_width=True,
        ):
            try:
                with st.spinner(
                    "Executing approved actions..."
                ):
                    resumed_result = run_workflow(
                        Command(
                            resume=build_review_response(
                                approval_request,
                                accepted=True,
                                feedback=feedback,
                            )
                        ),
                        st.session_state[
                            "workflow_config"
                        ],
                    )

                st.session_state[
                    "workflow_result"
                ] = resumed_result
                st.rerun()

            except Exception as error:
                st.exception(error)

        if reject_column.button(
            "Reject",
            use_container_width=True,
        ):
            try:
                resumed_result = run_workflow(
                    Command(
                        resume=build_review_response(
                            approval_request,
                            accepted=False,
                            feedback=feedback,
                        )
                    ),
                    st.session_state[
                        "workflow_config"
                    ],
                )

                st.session_state[
                    "workflow_result"
                ] = resumed_result
                st.rerun()

            except Exception as error:
                st.exception(error)

    else:
        stage = result.get("stage")

        if stage == "complete":
            st.success(
                "Incident workflow completed successfully."
            )
        elif stage == "rejected":
            st.warning(
                "The proposed actions were rejected."
            )
        elif result.get("decision") == "wait":
            st.info(
                "No immediate notification or Jira action "
                "is required."
            )