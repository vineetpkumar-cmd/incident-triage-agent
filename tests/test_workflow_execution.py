import pytest
from langgraph.types import Command

import src.nodes as nodes
from src.workflow import build_workflow


INCIDENT = {
    "number": "INC0010001",
    "short_description": "Email unavailable",
    "description": "Employees cannot send email.",
    "priority": "P1",
    "state": "New",
    "assignment_group": "Messaging Support",
    "engineering_required": True,
}


@pytest.mark.asyncio
async def test_approved_incident_completes_full_path(
    monkeypatch,
):
    calls = []

    async def fake_call_tool(tool_name, arguments):
        calls.append(tool_name)

        results = {
            "get_incident": INCIDENT,
            "get_incident_sla": {
                "incident_number": "INC0010001",
                "sla_breached": False,
            },
            "search_related_incidents": {
                "incident_number": "INC0010001",
                "related_incidents": [],
                "total": 0,
            },
            "search_jira_issues": {
                "incident_number": "INC0010001",
                "issues": [],
                "total": 0,
            },
            "create_email_draft": {
                "status": "drafted",
                "draft": {
                    "id": "DRAFT-TEST",
                    **arguments,
                },
            },
            "create_jira_issue": {
                "status": "created",
                "issue": {"key": "ENG-TEST"},
            },
            "send_email": {
                "status": "sent",
                "draft_id": "DRAFT-TEST",
            },
        }

        return results[tool_name]

    async def fake_generate_email_body(**kwargs):
        return "Ollama-generated incident notification."

    monkeypatch.setattr(
        nodes,
        "call_tool",
        fake_call_tool,
    )
    monkeypatch.setattr(
        nodes,
        "generate_email_body",
        fake_generate_email_body,
    )

    graph = build_workflow()
    config = {
        "configurable": {
            "thread_id": "full-path-test",
        }
    }

    result = await graph.ainvoke(
        {
            "incident_number": "INC0010001",
            "stage": "started",
            "retry_count": 0,
        },
        config=config,
    )

    assert result["evidence_status"] == "sufficient"
    assert result["draft_source"] == "ollama"
    assert result["email_body"] == (
        "Ollama-generated incident notification."
    )
    assert result["__interrupt__"][0].value[
        "review_type"
    ] == "action"
    assert "create_jira_issue" not in calls
    assert "send_email" not in calls

    result = await graph.ainvoke(
        Command(
            resume={
                "approved": True,
                "feedback": "Approved for test.",
            }
        ),
        config=config,
    )

    assert result["stage"] == "complete"
    assert result["jira_result"]["status"] == "created"
    assert result["send_result"]["status"] == "sent"
    assert calls == [
        "get_incident",
        "get_incident_sla",
        "search_related_incidents",
        "search_jira_issues",
        "create_email_draft",
        "create_jira_issue",
        "send_email",
    ]


@pytest.mark.asyncio
async def test_failed_retrieval_retries_then_asks_human(
    monkeypatch,
):
    calls = []

    async def missing_incident(tool_name, arguments):
        calls.append(tool_name)

        if tool_name != "get_incident":
            raise AssertionError(
                "No later tool should run without an incident."
            )

        return {"error": "Incident was not found."}

    monkeypatch.setattr(
        nodes,
        "call_tool",
        missing_incident,
    )

    graph = build_workflow()
    config = {
        "configurable": {
            "thread_id": "retrieval-review-test",
        }
    }

    result = await graph.ainvoke(
        {
            "incident_number": "INC0099999",
            "stage": "started",
            "retry_count": 0,
        },
        config=config,
    )

    review = result["__interrupt__"][0].value

    assert calls == ["get_incident", "get_incident"]
    assert result["retry_count"] == 1
    assert review["review_type"] == "retrieval"
    assert review["allowed_actions"] == ["retry", "stop"]
    assert any(
        item.startswith("incident.")
        for item in review["missing_evidence"]
    )

    result = await graph.ainvoke(
        Command(
            resume={
                "retry": False,
                "feedback": "Stop and investigate manually.",
            }
        ),
        config=config,
    )

    assert result["stage"] == "retrieval_stopped"
    assert "jira_result" not in result
    assert "send_result" not in result