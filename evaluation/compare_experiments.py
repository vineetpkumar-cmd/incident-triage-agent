"""Build one reproducible comparison from saved LangSmith case runs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable


METRICS = (
    "decision_and_tool_accuracy",
    "guardrail_compliance",
    "notification_quality",
    "task_completion",
    "trajectory_correctness",
)


def human_average(scores: Iterable[float]) -> float:
    """Return the arithmetic mean of the four human-judge dimensions."""
    values = list(scores)
    if len(values) != 4:
        raise ValueError("human judge average requires exactly four scores")
    return mean(values)


def aggregate_case_scores(cases: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    """Average each evaluator over cases where that evaluator produced a score."""
    metric_names = sorted(
        {
            metric
            for case in cases
            for metric in case.get("scores", {})
        }
    )
    aggregates: dict[str, dict[str, float | int]] = {}

    for metric in metric_names:
        values = [
            case["scores"].get(metric)
            for case in cases
            if case.get("scores", {}).get(metric) is not None
        ]
        if values:
            aggregates[metric] = {
                "mean": mean(values),
                "count": len(values),
            }

    return aggregates


def compare_case_outputs(
    baseline: list[dict[str, Any]],
    improved: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare two aligned sets of case outputs and retain failure evidence."""
    baseline_by_id = {case["case_id"]: case for case in baseline}
    improved_by_id = {case["case_id"]: case for case in improved}

    if set(baseline_by_id) != set(improved_by_id):
        raise ValueError("baseline and improved case IDs differ")

    def task_failures(cases_by_id: dict[str, dict[str, Any]]) -> list[str]:
        return sorted(
            case_id
            for case_id, case in cases_by_id.items()
            if case.get("scores", {}).get("task_completion") == 0
        )

    regressions = sorted(
        case_id
        for case_id in baseline_by_id
        if (
            baseline_by_id[case_id].get("scores", {}).get("task_completion")
            or 0
        )
        > (
            improved_by_id[case_id].get("scores", {}).get("task_completion")
            or 0
        )
    )

    return {
        "case_count": len(baseline_by_id),
        "baseline": aggregate_case_scores(baseline),
        "improved": aggregate_case_scores(improved),
        "task_completion_failures": {
            "baseline": task_failures(baseline_by_id),
            "improved": task_failures(improved_by_id),
        },
        "task_completion_regressions": regressions,
    }


def _score_from_stats(stats: dict[str, Any], metric: str) -> float | None:
    value = stats.get(metric, {}).get("avg")
    return float(value) if value is not None else None


def _export_project(client: Any, project_name: str) -> list[dict[str, Any]]:
    runs = list(client.list_runs(project_name=project_name, is_root=True))
    cases = []

    for run in runs:
        duration = None
        if run.end_time is not None:
            duration = (run.end_time - run.start_time).total_seconds()

        cases.append(
            {
                "case_id": run.inputs["case_id"],
                "run_id": str(run.id),
                "outputs": run.outputs,
                "scores": {
                    metric: _score_from_stats(run.feedback_stats or {}, metric)
                    for metric in METRICS
                },
                "latency_seconds": duration,
                "total_tokens": run.total_tokens or 0,
            }
        )

    return sorted(cases, key=lambda case: case["case_id"])


def _runtime_summary(cases: list[dict[str, Any]]) -> dict[str, float | int]:
    latencies = [
        case["latency_seconds"]
        for case in cases
        if case["latency_seconds"] is not None
    ]
    return {
        "median_latency_seconds": median(latencies),
        "total_tokens": sum(case["total_tokens"] for case in cases),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--improved", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation/canonical_comparison.json"),
    )
    args = parser.parse_args()

    from langsmith import Client

    client = Client(api_key=os.environ.get("LANGSMITH_API_KEY"))
    baseline = _export_project(client, args.baseline)
    improved = _export_project(client, args.improved)
    comparison = compare_case_outputs(baseline, improved)
    comparison["experiments"] = {
        "baseline": args.baseline,
        "improved": args.improved,
    }
    comparison["runtime"] = {
        "baseline": _runtime_summary(baseline),
        "improved": _runtime_summary(improved),
    }
    comparison["cases"] = {
        "baseline": baseline,
        "improved": improved,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output} from {comparison['case_count']} aligned cases")


if __name__ == "__main__":
    main()
