import pytest

import src.nodes as nodes


@pytest.mark.asyncio
async def test_incident_exception_becomes_state_error(
    monkeypatch,
):
    async def failing_tool(*args, **kwargs):
        raise RuntimeError("ServiceNow unavailable")

    monkeypatch.setattr(nodes, "call_tool", failing_tool)

    result = await nodes.retrieve_incident(
        {"incident_number": "INC0010001"}
    )

    assert result["incident"] == {}
    assert "get_incident failed" in result["error"]
    assert result["stage"] == "incident_retrieval_failed"


@pytest.mark.asyncio
async def test_enrichment_collects_partial_failures(
    monkeypatch,
):
    async def partly_failing_tool(tool_name, arguments):
        if tool_name == "get_incident_sla":
            raise RuntimeError("SLA unavailable")

        return {
            "incident_number": arguments["incident_number"],
            "related_incidents": [],
            "total": 0,
        }

    monkeypatch.setattr(
        nodes,
        "call_tool",
        partly_failing_tool,
    )

    result = await nodes.enrich_incident(
        {"incident_number": "INC0010001"}
    )

    assert result["sla"] == {}
    assert result["related_incidents"]["total"] == 0
    assert "get_incident_sla failed" in result["error"]
    assert result["stage"] == "incident_enrichment_failed"


@pytest.mark.asyncio
async def test_jira_exception_becomes_state_error(
    monkeypatch,
):
    async def failing_tool(*args, **kwargs):
        raise RuntimeError("Jira unavailable")

    monkeypatch.setattr(nodes, "call_tool", failing_tool)

    result = await nodes.search_jira(
        {"incident_number": "INC0010001"}
    )

    assert result["jira_search"] == {}
    assert "search_jira_issues failed" in result["error"]
    assert result["stage"] == "jira_search_failed"