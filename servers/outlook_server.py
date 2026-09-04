import json
import os
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Mock Outlook")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = Path(
    os.getenv(
        "OUTLOOK_DATA_FILE",
        str(PROJECT_ROOT / "data" / "notifications.json"),
    )
)

ALLOWED_RECIPIENTS = {
    "incident-management@example.com",
    "messaging-support@example.com",
    "business-apps@example.com",
}


def load_notifications() -> dict:
    """Load fictional Outlook data."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_notifications(data: dict) -> None:
    """Save fictional Outlook data."""
    DATA_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


@mcp.tool()
def create_email_draft(
    recipients: list[str],
    subject: str,
    body: str,
    incident_number: str,
) -> dict:
    """Create an Outlook email draft without sending it."""
    recipients = [
        recipient.strip().lower()
        for recipient in recipients
    ]
    subject = subject.strip()
    body = body.strip()
    incident_number = incident_number.strip().upper()

    if not re.fullmatch(r"INC\d{7}", incident_number):
        return {
            "status": "blocked",
            "reason": "Invalid incident number.",
        }

    if not recipients:
        return {
            "status": "blocked",
            "reason": "At least one recipient is required.",
        }

    if any(
        recipient not in ALLOWED_RECIPIENTS
        for recipient in recipients
    ):
        return {
            "status": "blocked",
            "reason": "Recipient is not allowed.",
        }

    if not subject or not body:
        return {
            "status": "blocked",
            "reason": "Subject and body are required.",
        }

    data = load_notifications()
    next_number = len(data["email_drafts"]) + 1
    draft_id = f"DRAFT-{next_number:03d}"

    draft = {
        "id": draft_id,
        "recipients": recipients,
        "subject": subject,
        "body": body,
        "incident_number": incident_number,
        "sent": False,
    }

    data["email_drafts"].append(draft)
    save_notifications(data)

    return {
        "status": "drafted",
        "draft": draft,
    }
@mcp.tool()
def send_email(
    draft_id: str,
    incident_priority: str,
    approved: bool = False,
) -> dict:
    """Send an existing fictional Outlook draft."""
    draft_id = draft_id.strip().upper()
    incident_priority = incident_priority.strip().upper()

    data = load_notifications()

    for draft in data["email_drafts"]:
        if draft["id"] != draft_id:
            continue

        if draft["sent"]:
            return {
                "status": "blocked",
                "reason": "Email draft has already been sent.",
            }

        if (
            incident_priority in {"P1", "P2"}
            and not approved
        ):
            return {
                "status": "approval_required",
                "reason": (
                    f"{incident_priority} emails require "
                    "human approval."
                ),
            }

        draft["sent"] = True
        sent_email = draft.copy()
        data["sent_emails"].append(sent_email)
        save_notifications(data)

        return {
            "status": "sent",
            "email": sent_email,
        }

    return {
        "status": "not_found",
        "reason": f"Email draft {draft_id} was not found.",
    }

if __name__ == "__main__":
    mcp.run()
