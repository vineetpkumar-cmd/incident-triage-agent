from langsmith import Client

from evaluation import (
    DATASET_NAME,
    DATASET_VERSION,
)
from evaluation.cases import load_cases


def to_langsmith_example(case: dict) -> dict:
    """Split one case into LangSmith dataset fields."""
    input_keys = (
        "case_id",
        "incident",
        "jira_issues",
        "approval_response",
        "fault",
    )

    return {
        "inputs": {
            key: case[key]
            for key in input_keys
            if key in case
        },
        "outputs": case["expected"],
        "metadata": {
            "case_id": case["case_id"],
            "scenario_type": case["scenario_type"],
            "difficulty": case["difficulty"],
            "dataset_version": DATASET_VERSION,
            "rationale": case["rationale"],
        },
    }


def upload_dataset(client: Client) -> str:
    """Create and populate the LangSmith dataset."""
    if client.has_dataset(
        dataset_name=DATASET_NAME
    ):
        raise RuntimeError(
            f"Dataset {DATASET_NAME!r} already exists"
        )

    dataset = client.create_dataset(
        DATASET_NAME,
        description=(
            "40 fictional Incident Triage Agent "
            "evaluation cases."
        ),
        metadata={
            "version": DATASET_VERSION,
            "contains_real_data": False,
        },
    )

    examples = [
        to_langsmith_example(case)
        for case in load_cases()
    ]

    client.create_examples(
        dataset_id=dataset.id,
        examples=examples,
    )

    return str(dataset.id)


if __name__ == "__main__":
    print(
        "Created dataset:",
        upload_dataset(Client()),
    )