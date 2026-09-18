"""Render submission-ready Week 6 red-team findings from canonical evidence."""

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFENSES = {
    "jailbreaking": "Input instruction-hierarchy guardrail",
    "prompt_injection": "Inspect user, incident, and Jira text before execution",
    "obfuscation": "Encoded/spaced-text detection and safe review",
    "pii_extraction": "Sensitive-data request blocking and output PII scan",
    "tool_abuse": "Deterministic tool allowlist, scope, stage, and approval checks",
    "social_engineering": "Authority claims route to review; backend approval remains authoritative",
    "crescendo": "Inspect the complete conversation and all untrusted source text",
    "internal_disclosure": "Internal-topic input block and output disclosure scan",
    "legitimate_control": "Permit normal scoped workflow behavior; monitor overblocking",
}


def _cell(value: Any, limit: int = 220) -> str:
    text = str(value or "").replace("\n", " ").replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _rates(evidence: list[dict[str, Any]]) -> tuple[int, int]:
    attacks = [row for row in evidence if row["attack_family"] != "legitimate_control"]
    controls = [row for row in evidence if row["attack_family"] == "legitimate_control"]
    return len(attacks), len(controls)


def _evidence_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Case | Family | Prompt | Observed result | Verdict | Recommended defense |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        observed = row.get("response") or "; ".join(row.get("reasons", [])) or "No visible response"
        tools = ", ".join(row.get("tool_sequence", []))
        if tools:
            observed = f"{observed} Tools: {tools}."
        lines.append(
            f"| {_cell(row['case_id'])} | {_cell(row['attack_family'])} | "
            f"{_cell(' / '.join(row.get('turns', [])))} | {_cell(observed)} | "
            f"{_cell(row['verdict'])} | {_cell(DEFENSES[row['attack_family']])} |"
        )
    return "\n".join(lines)


def render_report(
    baseline: list[dict[str, Any]],
    defended: list[dict[str, Any]],
    comparison: dict[str, Any],
) -> str:
    """Render a deterministic Markdown report with denominators and case evidence."""

    defended_by_id = {row["case_id"]: row for row in defended}
    attacks = [row for row in defended if row["attack_family"] != "legitimate_control"]
    controls = [row for row in defended if row["attack_family"] == "legitimate_control"]
    attack_count, control_count = _rates(defended)
    base = comparison["baseline"]
    protected = comparison["defended"]
    transition_text = ", ".join(
        f"{name}: {count}" for name, count in comparison.get("transitions", {}).items()
    ) or "No verdict changes"
    remaining = comparison.get("remaining_failures", [])
    regressions = comparison.get("utility_regressions", [])

    sections = [
        "# Week 6 Incident Triage Red-Team Findings",
        "",
        "![Week 6 red-team architecture](week6-red-team-architecture.svg)",
        "",
        "## Executive summary",
        "",
        "This Path B project red-teams the existing Incident Triage Agent using 24 fictional attacks "
        "and six legitimate-use controls. Baseline and defended modes ran the same 30 case IDs in "
        "isolated temporary ServiceNow, Jira, and Outlook stores. No production data or public LLM endpoint was used.",
        "",
        f"Attack safety PASS improved from {base['safety_pass_rate']:.0%} (0/{attack_count} in the canonical run) "
        f"to {protected['safety_pass_rate']:.0%} ({sum(r['verdict']=='PASS' for r in attacks)}/{attack_count}). "
        f"Legitimate-control completion remained {protected['control_completion_rate']:.0%} "
        f"({sum(r['verdict']=='PASS' for r in controls)}/{control_count}).",
        "",
        "The baseline produced WARN rather than FAIL for the 24 attacks: it did not perform the requested "
        "unsafe action, but it also did not clearly refuse the malicious intent. This distinction is retained rather than overstated.",
        "",
        "## Baseline vs defended results",
        "",
        "| Mode | PASS | WARN | FAIL | Attack safety PASS | Control completion |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Baseline | {base['pass']} | {base['warn']} | {base['fail']} | {base['safety_pass_rate']:.0%} | {base['control_completion_rate']:.0%} |",
        f"| Defended | {protected['pass']} | {protected['warn']} | {protected['fail']} | {protected['safety_pass_rate']:.0%} | {protected['control_completion_rate']:.0%} |",
        "",
        f"Verdict transitions: {transition_text}.",
        "",
        "## Attack evidence",
        "",
        _evidence_table(attacks),
        "",
        "## Legitimate-use controls",
        "",
        _evidence_table(controls),
        "",
        "## Attack-to-defense mapping",
        "",
        "| Attack family | Implemented control |",
        "|---|---|",
        *[f"| {family} | {_cell(defense)} |" for family, defense in DEFENSES.items() if family != "legitimate_control"],
        "",
        "## Remaining failures and next experiments",
        "",
        f"Remaining FAIL cases: {', '.join(remaining) if remaining else 'None in this fictional evaluation.'}",
        "",
        f"Utility regressions: {', '.join(regressions) if regressions else 'None. CTRL-006 remains WARN in both modes because rejection is intentional.'}",
        "",
        "Next experiments: test paraphrases not present in the fixed suite, add anonymized production-shaped fixtures "
        "after governance approval, measure false-positive rates, and expand cross-case mutation telemetry.",
        "",
        "## Evidence and responsible use",
        "",
        "All records, identities, addresses, and integration stores are fictional. The figures are specific to this "
        "local mock environment and must not be presented as production security assurance.",
        "",
        "## Screenshot checklist",
        "",
        "1. Baseline WARN example showing malicious intent was not clearly refused.",
        "2. The same case PASS in defended mode with its guardrail event.",
        "3. CTRL-006 WARN showing intentional P1 rejection.",
        "4. A legitimate PASS control such as CTRL-001.",
        "5. The baseline-versus-defended summary table.",
        "",
    ]
    return "\n".join(sections)


def write_defense_csv(path: Path, defended: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case", "family", "prompt", "observed_result", "verdict", "recommended_defense"])
        for row in defended:
            writer.writerow([
                row["case_id"], row["attack_family"], " / ".join(row.get("turns", [])),
                row.get("response", ""), row["verdict"], DEFENSES[row["attack_family"]],
            ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--defended", required=True, type=Path)
    parser.add_argument("--comparison", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--csv", type=Path, default=Path("red_team/results/defense_table.csv"))
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    defended = json.loads(args.defended.read_text(encoding="utf-8"))
    comparison = json.loads(args.comparison.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(baseline, defended, comparison), encoding="utf-8")
    write_defense_csv(args.csv, defended)
    print(f"Wrote report to {args.output} and defense table to {args.csv}")


if __name__ == "__main__":
    main()
