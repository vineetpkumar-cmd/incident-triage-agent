import json

import servers.jira_server as jira_server


def use_temporary_jira_file(tmp_path, monkeypatch, issues):
    data_file = tmp_path / "jira_issues.json"
    data_file.write_text(
        json.dumps(issues),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        jira_server,
        "DATA_FILE",
        data_file,
    )


def test_search_jira_issues_by_incident_number():
    result = jira_server.search_jira_issues("INC0010002")

    assert result["total"] == 1
    assert result["issues"][0]["key"] == "ENG-101"
    assert result["issues"][0]["issue_type"] == "Story"


def test_create_approved_jira_story(tmp_path, monkeypatch):
    use_temporary_jira_file(tmp_path, monkeypatch, [])

    assert hasattr(jira_server, "create_jira_issue")

    result = jira_server.create_jira_issue(
        project="ENG",
        issue_type="Story",
        summary="Investigate email outage",
        description="Investigate incident INC0010001.",
        jira_priority="Highest",
        linked_incident="INC0010001",
        incident_priority="P1",
        approved=True,
    )

    assert result["status"] == "created"
    assert result["issue"]["key"] == "ENG-101"
    assert result["issue"]["issue_type"] == "Story"


def test_create_jira_issue_requires_approval(
    tmp_path,
    monkeypatch,
):
    use_temporary_jira_file(tmp_path, monkeypatch, [])

    result = jira_server.create_jira_issue(
        project="ENG",
        issue_type="Story",
        summary="Investigate email outage",
        description="Investigate incident INC0010001.",
        jira_priority="Highest",
        linked_incident="INC0010001",
        incident_priority="P1",
        approved=False,
    )

    assert result["status"] == "approval_required"


def test_create_jira_issue_prevents_duplicate(
    tmp_path,
    monkeypatch,
):
    existing_issue = {
        "key": "ENG-101",
        "project": "ENG",
        "issue_type": "Story",
        "summary": "Existing investigation",
        "description": "Existing investigation.",
        "status": "Open",
        "priority": "High",
        "linked_incident": "INC0010001",
        "comments": [],
    }
    use_temporary_jira_file(
        tmp_path,
        monkeypatch,
        [existing_issue],
    )

    result = jira_server.create_jira_issue(
        project="ENG",
        issue_type="Story",
        summary="Duplicate investigation",
        description="This should not be created.",
        jira_priority="Highest",
        linked_incident="INC0010001",
        incident_priority="P1",
        approved=True,
    )

    assert result["status"] == "blocked"
    assert result["existing_issue"] == "ENG-101"

def test_create_rejects_invalid_incident_number(
    tmp_path,
    monkeypatch,
):
    use_temporary_jira_file(tmp_path, monkeypatch, [])

    result = jira_server.create_jira_issue(
        project="ENG",
        issue_type="Story",
        summary="Invalid linked incident",
        description="This issue should not be created.",
        jira_priority="High",
        linked_incident="NC0010001",
        incident_priority="P3",
        approved=False,
    )

    assert result["status"] == "blocked"
    assert result["reason"] == (
        "Linked incident must match INC followed by "
        "seven digits."
    )
    assert jira_server.load_jira_issues() == []

def test_add_jira_comment(tmp_path, monkeypatch):
    existing_issue = {
        "key": "ENG-101",
        "project": "ENG",
        "issue_type": "Story",
        "summary": "Investigate service outage",
        "description": "Engineering investigation.",
        "status": "Open",
        "priority": "High",
        "linked_incident": "INC0010001",
        "comments": [],
    }
    use_temporary_jira_file(
        tmp_path,
        monkeypatch,
        [existing_issue],
    )

    assert hasattr(jira_server, "add_jira_comment")

    result = jira_server.add_jira_comment(
        issue_key="ENG-101",
        comment="ServiceNow incident has been escalated.",
        incident_priority="P3",
        approved=False,
    )

    assert result["status"] == "updated"
    assert result["issue_key"] == "ENG-101"
    assert result["comment"] == (
        "ServiceNow incident has been escalated."
    )

    saved_issues = jira_server.load_jira_issues()
    assert saved_issues[0]["comments"] == [
        "ServiceNow incident has been escalated."
    ]


def test_add_jira_comment_rejects_empty_comment(
    tmp_path,
    monkeypatch,
):
    use_temporary_jira_file(tmp_path, monkeypatch, [])

    result = jira_server.add_jira_comment(
        issue_key="ENG-101",
        comment="   ",
        incident_priority="P3",
        approved=False,
    )

    assert result["status"] == "blocked"
    assert result["reason"] == "Comment cannot be empty."


def test_add_jira_comment_requires_p1_approval(
    tmp_path,
    monkeypatch,
):
    use_temporary_jira_file(tmp_path, monkeypatch, [])

    result = jira_server.add_jira_comment(
        issue_key="ENG-101",
        comment="Major incident update.",
        incident_priority="P1",
        approved=False,
    )

    assert result["status"] == "approval_required"


def test_add_comment_handles_unknown_issue(
    tmp_path,
    monkeypatch,
):
    use_temporary_jira_file(tmp_path, monkeypatch, [])

    result = jira_server.add_jira_comment(
        issue_key="ENG-999",
        comment="Incident update.",
        incident_priority="P3",
        approved=False,
    )

    assert result["status"] == "not_found"