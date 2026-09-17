from typing import Any, Literal, NotRequired, TypedDict

AttackFamily = Literal[
    "jailbreaking",
    "prompt_injection",
    "obfuscation",
    "pii_extraction",
    "tool_abuse",
    "social_engineering",
    "crescendo",
    "internal_disclosure",
    "legitimate_control",
]
Verdict = Literal["PASS", "WARN", "FAIL"]


class ExpectedBehavior(TypedDict):
    allowed_tools: list[str]
    prohibited_tools: list[str]
    must_refuse: bool
    must_not_leak: list[str]
    writes_allowed: bool


class AttackCase(TypedDict):
    case_id: str
    attack_family: AttackFamily
    title: str
    turns: list[str]
    incident: dict[str, Any]
    jira_issues: list[dict[str, Any]]
    approval_response: NotRequired[dict[str, Any]]
    expected: ExpectedBehavior


class CaseEvidence(TypedDict):
    case_id: str
    mode: Literal["baseline", "defended"]
    attack_family: AttackFamily
    turns: list[str]
    response: str
    final_state: dict[str, Any]
    tool_sequence: list[str]
    tool_arguments: list[dict[str, Any]]
    mutations: dict[str, Any]
    guardrail_events: list[dict[str, Any]]
    error: str | None
    verdict: Verdict
    reasons: list[str]


FAMILIES = {
    "jailbreaking", "prompt_injection", "obfuscation",
    "pii_extraction", "tool_abuse", "social_engineering",
    "crescendo", "internal_disclosure", "legitimate_control",
}


def validate_case(case: AttackCase) -> None:
    required = {"case_id", "attack_family", "title", "turns", "incident", "jira_issues", "expected"}
    missing = sorted(required - case.keys())
    if missing:
        raise ValueError(f"missing case fields: {missing}")
    if case["attack_family"] not in FAMILIES:
        raise ValueError(f"unknown attack_family: {case['attack_family']}")
    expected_required = {"allowed_tools", "prohibited_tools", "must_refuse", "must_not_leak", "writes_allowed"}
    expected_missing = sorted(expected_required - case["expected"].keys())
    if expected_missing:
        raise ValueError(f"missing expected fields: {expected_missing}")
    if not case["turns"]:
        raise ValueError("turns must not be empty")
