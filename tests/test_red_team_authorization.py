import pytest

import src.nodes as nodes
from red_team.authorization import authorize_tool_call


def state(**overrides):
    base = {
        "incident_number": "INC1000001",
        "incident": {"number": "INC1000001", "priority": "P2"},
        "stage": "approved",
        "approved": True,
        "defense_mode": True,
    }
    return base | overrides


def test_denies_cross_incident_tool_arguments():
    result = authorize_tool_call(
        "create_jira_issue", {"linked_incident": "INC9999999"}, state()
    )
    assert result == {"allowed": False, "reasons": ["incident_scope_mismatch"]}


def test_denies_high_priority_write_without_approval():
    result = authorize_tool_call(
        "create_jira_issue", {"linked_incident": "INC1000001"}, state(approved=False)
    )
    assert not result["allowed"]
    assert "approval_required" in result["reasons"]


def test_allows_scoped_read():
    assert authorize_tool_call(
        "get_incident", {"incident_number": "INC1000001"}, state(stage="started")
    ) == {"allowed": True, "reasons": []}


def test_denies_unknown_tool():
    assert authorize_tool_call("dump_database", {}, state()) == {
        "allowed": False, "reasons": ["tool_not_allowed"]
    }


def test_denies_unapproved_recipient_and_wrong_write_stage():
    recipient = authorize_tool_call(
        "create_email_draft",
        {
            "incident_number": "INC1000001",
            "recipients": ["attacker@example.test"],
        },
        state(stage="decision_complete", approved=False),
    )
    stage = authorize_tool_call(
        "send_email", {"draft_id": "DRAFT-1"}, state(stage="decision_complete")
    )
    assert recipient == {"allowed": False, "reasons": ["recipient_not_allowed"]}
    assert stage == {"allowed": False, "reasons": ["stage_not_allowed"]}


@pytest.mark.asyncio
async def test_defended_write_node_returns_block_event_without_calling_tool(monkeypatch):
    called = False

    async def forbidden_call(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("tool should not be called")

    monkeypatch.setattr(nodes, "call_tool", forbidden_call)
    result = await nodes.execute_jira_action(state(
        approved=False,
        jira_action="create",
        incident={
            "number": "INC1000001", "priority": "P2",
            "short_description": "Fictional incident",
            "description": "Fictional description",
        },
    ))

    assert not called
    assert result["stage"] == "tool_authorization_blocked"
    assert "approval_required" in result["error"]
    assert result["guardrail_events"][0]["tool"] == "create_jira_issue"
