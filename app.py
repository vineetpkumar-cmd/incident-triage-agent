import asyncio
import json
import uuid

from langgraph.types import Command

from src.review import (
    build_review_response,
    is_retrieval_review,
)

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

    while interrupts:
        review_request = interrupts[0].value

        print_json(
            "Human review required:",
            review_request,
        )

        retrieval_review = is_retrieval_review(
            review_request
        )

        question = (
            "\nRetry retrieval? (yes/no): "
            if retrieval_review
            else "\nApprove these actions? (yes/no): "
        )

        answer = input(question).strip().lower()
        accepted = answer in {"yes", "y"}

        feedback = input(
            "Optional feedback: "
        ).strip()

        resume_payload = build_review_response(
            review_request,
            accepted=accepted,
            feedback=feedback,
        )

        result = await workflow.ainvoke(
            Command(resume=resume_payload),
            config=config,
        )

        interrupts = result.get("__interrupt__", [])
    print_json(
        "Final workflow state:",
        result,
    )

    stage = result.get("stage", "unknown")
    print(f"\nWorkflow finished at stage: {stage}")


if __name__ == "__main__":
    asyncio.run(run_incident())