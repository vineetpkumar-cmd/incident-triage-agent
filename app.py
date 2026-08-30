import asyncio
import json
import uuid

from langgraph.types import Command

from src.workflow import workflow


def print_json(title: str, value) -> None:
    """Print readable JSON output."""
    print(f"\n{title}")
    print(json.dumps(value, indent=2, default=str))


async def run_incident() -> None:
    """Run one fictional incident through LangGraph."""
    incident_number = input(
        "Enter a ServiceNow incident number: "
    ).strip().upper()

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

    print("\nStarting incident triage workflow...")

    result = await workflow.ainvoke(
        initial_state,
        config=config,
    )

    interrupts = result.get("__interrupt__", [])

    if interrupts:
        approval_request = interrupts[0].value

        print_json(
            "Human approval required:",
            approval_request,
        )

        answer = input(
            "\nApprove these actions? (yes/no): "
        ).strip().lower()

        approved = answer in {"yes", "y"}

        feedback = input(
            "Optional feedback: "
        ).strip()

        result = await workflow.ainvoke(
            Command(
                resume={
                    "approved": approved,
                    "feedback": feedback,
                }
            ),
            config=config,
        )

    print_json(
        "Final workflow state:",
        result,
    )

    stage = result.get("stage", "unknown")
    print(f"\nWorkflow finished at stage: {stage}")


if __name__ == "__main__":
    asyncio.run(run_incident())