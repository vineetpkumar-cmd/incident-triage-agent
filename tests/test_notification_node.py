import pytest

import src.nodes as nodes


STATE = {
    "incident_number": "INC0010001",
    "incident": {
        "number": "INC0010001",
        "priority": "P1",
        "short_description": "Email unavailable",
        "description": (
            "Fictional email service is unavailable."
        ),
        "assignment_group": "Messaging Support",
    },
    "jira_search": {
        "total": 0,
        "issues": [],
    },
    "decision": "escalate",
}


async def fake_draft_tool(
    tool_name,
    arguments,
):
    assert tool_name == "create_email_draft"
    return {
        "status": "drafted",
        "draft": {
            "id": "DRAFT-TEST",
            **arguments,
        },
    }


@pytest.mark.asyncio
async def test_prepare_notification_uses_ollama(
    monkeypatch,
):
    async def fake_generate(*args, **kwargs):
        return "Locally generated factual notification."

    monkeypatch.setattr(
        nodes,
        "generate_email_body",
        fake_generate,
    )
    monkeypatch.setattr(
        nodes,
        "call_tool",
        fake_draft_tool,
    )

    result = await nodes.prepare_notification(STATE)

    assert result["email_body"] == (
        "Locally generated factual notification."
    )
    assert result["draft_source"] == "ollama"
    assert result["model_error"] is None


@pytest.mark.asyncio
async def test_prepare_notification_falls_back_when_ollama_fails(
    monkeypatch,
):
    async def failing_generate(*args, **kwargs):
        raise RuntimeError("Ollama unavailable")

    monkeypatch.setattr(
        nodes,
        "generate_email_body",
        failing_generate,
    )
    monkeypatch.setattr(
        nodes,
        "call_tool",
        fake_draft_tool,
    )

    result = await nodes.prepare_notification(STATE)

    assert "INC0010001" in result["email_body"]
    assert result["draft_source"] == (
        "template_fallback"
    )
    assert result["model_error"] == "RuntimeError"
