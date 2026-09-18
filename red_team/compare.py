"""Aligned baseline-versus-defended red-team comparison."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed = {row["case_id"]: row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError("duplicate case IDs")
    return indexed


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["verdict"] for row in rows)
    attacks = [row for row in rows if row["attack_family"] != "legitimate_control"]
    controls = [row for row in rows if row["attack_family"] == "legitimate_control"]
    by_family: dict[str, dict[str, int]] = defaultdict(lambda: {"pass": 0, "warn": 0, "fail": 0})
    for row in rows:
        by_family[row["attack_family"]][row["verdict"].casefold()] += 1
    return {
        "pass": counts["PASS"],
        "warn": counts["WARN"],
        "fail": counts["FAIL"],
        "safety_pass_rate": (
            sum(row["verdict"] == "PASS" for row in attacks) / len(attacks) if attacks else 0.0
        ),
        "control_completion_rate": (
            sum(row["verdict"] == "PASS" for row in controls) / len(controls) if controls else 0.0
        ),
        "by_family": dict(sorted(by_family.items())),
    }


def compare_runs(
    baseline: list[dict[str, Any]], defended: list[dict[str, Any]]
) -> dict[str, Any]:
    """Compare aligned case evidence and keep failures/regressions explicit."""

    base_by_id = _index(baseline)
    defended_by_id = _index(defended)
    if set(base_by_id) != set(defended_by_id):
        raise ValueError("case IDs differ between baseline and defended runs")

    transitions: Counter[str] = Counter()
    remaining_failures: list[str] = []
    utility_regressions: list[str] = []
    for case_id in base_by_id:
        before = base_by_id[case_id]
        after = defended_by_id[case_id]
        transition = f"{before['verdict']}->{after['verdict']}"
        if before["verdict"] != after["verdict"]:
            transitions[transition] += 1
        if after["verdict"] == "FAIL":
            remaining_failures.append(case_id)
        if (
            before["attack_family"] == "legitimate_control"
            and before["verdict"] == "PASS"
            and after["verdict"] != "PASS"
        ):
            utility_regressions.append(case_id)

    return {
        "case_count": len(baseline),
        "baseline": _summary(baseline),
        "defended": _summary(defended),
        "transitions": dict(transitions),
        "remaining_failures": remaining_failures,
        "utility_regressions": utility_regressions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--defended", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    defended = json.loads(args.defended.read_text(encoding="utf-8"))
    result = compare_runs(baseline, defended)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
