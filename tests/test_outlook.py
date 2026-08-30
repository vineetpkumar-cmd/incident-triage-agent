import json

import servers.outlook_server as outlook_server


def use_temporary_notifications_file(
    tmp_path,
    monkeypatch,
):
    data_file = tmp_path / "notifications.json"
    data_file.write_text(
        json.dumps(
            {
                "email_drafts": [],
                "sent_emails": [],
                "calendar_holds": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        outlook_server,
        "DATA_FILE",
        data_file,
    )


def test_create_email_draft(tmp_path, monkeypatch):
    use_temporary_notifications_file(
        tmp_path,
        monkeypatch,
    )

    assert hasattr(outlook_server, "create_email_draft")

    result = outlook_server.create_email_draft(
        recipients=[
            "incident-management@example.com",
        ],
        subject="P1 incident INC0010001",
        body="The email service is unavailable.",
        incident_number="INC0010001",
    )

    assert result["status"] == "drafted"
    assert result["draft"]["id"] == "DRAFT-001"
    assert result["draft"]["sent"] is False

    saved_data = outlook_server.load_notifications()
    assert len(saved_data["email_drafts"]) == 1
    assert saved_data["sent_emails"] == []


def test_email_draft_rejects_external_recipient(
    tmp_path,
    monkeypatch,
):
    use_temporary_notifications_file(
        tmp_path,
        monkeypatch,
    )

    result = outlook_server.create_email_draft(
        recipients=["person@external-company.com"],
        subject="P1 incident INC0010001",
        body="Confidential incident information.",
        incident_number="INC0010001",
    )

    assert result["status"] == "blocked"
    assert result["reason"] == "Recipient is not allowed."
def create_test_draft():
    return outlook_server.create_email_draft(
        recipients=[
            "incident-management@example.com",
        ],
        subject="P1 incident INC0010001",
        body="The email service is unavailable.",
        incident_number="INC0010001",
    )


def test_send_email_requires_p1_approval(
    tmp_path,
    monkeypatch,
):
    use_temporary_notifications_file(
        tmp_path,
        monkeypatch,
    )
    create_test_draft()

    assert hasattr(outlook_server, "send_email")

    result = outlook_server.send_email(
        draft_id="DRAFT-001",
        incident_priority="P1",
        approved=False,
    )

    assert result["status"] == "approval_required"

    saved_data = outlook_server.load_notifications()
    assert saved_data["sent_emails"] == []


def test_send_approved_email(tmp_path, monkeypatch):
    use_temporary_notifications_file(
        tmp_path,
        monkeypatch,
    )
    create_test_draft()

    result = outlook_server.send_email(
        draft_id="DRAFT-001",
        incident_priority="P1",
        approved=True,
    )

    assert result["status"] == "sent"
    assert result["email"]["id"] == "DRAFT-001"
    assert result["email"]["sent"] is True

    saved_data = outlook_server.load_notifications()
    assert len(saved_data["sent_emails"]) == 1


def test_email_cannot_be_sent_twice(
    tmp_path,
    monkeypatch,
):
    use_temporary_notifications_file(
        tmp_path,
        monkeypatch,
    )
    create_test_draft()

    outlook_server.send_email(
        draft_id="DRAFT-001",
        incident_priority="P1",
        approved=True,
    )

    second_result = outlook_server.send_email(
        draft_id="DRAFT-001",
        incident_priority="P1",
        approved=True,
    )

    assert second_result["status"] == "blocked"
    assert second_result["reason"] == (
        "Email draft has already been sent."
    )