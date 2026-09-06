import argparse
import asyncio

from langsmith import Client

from evaluation import (
    AGENT_VERSION,
    DATASET_NAME,
    DATASET_VERSION,
    PROMPT_VERSION,
)
from evaluation.evaluators import (
    DETERMINISTIC_EVALUATORS,
)
from evaluation.ollama_judge import (
    notification_quality,
)
from evaluation.runner import run_case


async def run_improved(
    case_ids: set[str] | None = None,
):
    """Run the improved evaluation in LangSmith."""
    client = Client()

    examples = list(
        client.list_examples(
            dataset_name=DATASET_NAME,
        )
    )

    if case_ids:
        examples = [
            example
            for example in examples
            if example.inputs.get("case_id")
            in case_ids
        ]

    return await client.aevaluate(
        run_case,
        data=examples,
        evaluators=[
            *DETERMINISTIC_EVALUATORS,
            notification_quality,
        ],
        experiment_prefix=(
            "incident-triage-improved"
        ),
        description=(
        "Week 4 improved incident triage agent."
        ),
        metadata={
            "agent_version": "week4-improved-v1",
            "prompt_version": PROMPT_VERSION,
            "dataset_version": DATASET_VERSION,
            "environment": "local-fictional",
        },
        max_concurrency=1,
        error_handling="log",
    )


def parse_case_ids(value: str | None):
    """Convert comma-separated case IDs to a set."""
    if not value:
        return None

    return {
        case_id.strip()
        for case_id in value.split(",")
        if case_id.strip()
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run the Incident Triage LangSmith "
            "baseline evaluation."
        )
    )

    parser.add_argument(
        "--case-ids",
        help=(
            "Optional comma-separated case IDs, "
            "for example HP-001,EDGE-001."
        ),
    )

    arguments = parser.parse_args()

    asyncio.run(
        run_improved(
            parse_case_ids(arguments.case_ids)
        )
    )


if __name__ == "__main__":
    main()