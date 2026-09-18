# Task 2 Report: Attack and Legitimate-Control Library

## Status

Complete. Task 2 adds the canonical Week 6 red-team case library and strengthens the library-quality tests with exact attack-family cardinality checks.

## Files

- Created `red_team/cases.py` with the specified 24 attack records and six legitimate controls.
- Modified `tests/test_red_team_cases.py` with library count, uniqueness/validation, no-write, and exact-family assertions.

## Verification

Focused RED command (initial worktree command; unavailable interpreter):

```text
LANGSMITH_TRACING=false .venv/bin/python -m pytest -p no:cacheprovider tests/test_red_team_cases.py -v
zsh:1: no such file or directory: .venv/bin/python
```

Focused RED command (using the repository virtualenv):

```text
LANGSMITH_TRACING=false /Users/testuser/incident-triage-agent/.venv/bin/python -m pytest -p no:cacheprovider tests/test_red_team_cases.py -v
```

Result: collection failed as expected with `ModuleNotFoundError: No module named 'red_team.cases'`.

Focused GREEN command:

```text
LANGSMITH_TRACING=false /Users/testuser/incident-triage-agent/.venv/bin/python -m pytest -p no:cacheprovider tests/test_red_team_cases.py -v
```

Result: `6 passed`.

Full suite command (run once):

```text
LANGSMITH_TRACING=false /Users/testuser/incident-triage-agent/.venv/bin/python -m pytest -p no:cacheprovider
```

Result: `74 passed in 0.59s`.

## Commit

`89451797d9638caf480c72c29c3efbb93fc135da` — `test: add Week 6 red-team case library`

## Assumptions

- All incident numbers, Jira keys, descriptions, and prompts are fictional local fixtures.
- Attack cases default to read-only expectations and denied approval; the approved Jira control is the sole write-allowed control.
- The existing Task 1 `AttackCase` and `validate_case` contracts are authoritative.

## Concerns

- The requested worktree does not contain its own `.venv`; verification used the parent repository virtualenv at `/Users/testuser/incident-triage-agent/.venv/bin/python`.

## Review Fix Round

Addressed review findings by adding executable incident fields and valid unique `INC#######` identifiers, concrete attack payloads (including injected incident/Jira content, Base64 and spaced obfuscation, authority/urgency claims, and crescendo actions), exact workflow tool names, scenario-specific leak policies, realistic control priorities/Jira links, and preservation of explicit empty prohibited-tool lists. Added focused tests for each of these behaviors before implementation.

Focused red test:

```text
LANGSMITH_TRACING=false /Users/testuser/incident-triage-agent/.venv/bin/python -m pytest -p no:cacheprovider tests/test_red_team_cases.py -v
```

Result before fixes: `6 passed, 3 failed` with expected failures for fixture shape/IDs, concrete payloads, and control policies.

Focused green result: `9 passed`.

Full suite (run once after fixes):

```text
LANGSMITH_TRACING=false /Users/testuser/incident-triage-agent/.venv/bin/python -m pytest -p no:cacheprovider
```

Result: `77 passed in 0.58s`.

Fix commit: `94ed9ae1f4f75faebf6cc14125cdf5a220b56977` (`fix: harden Week 6 red-team case fixtures`).

## Re-review Fix Round

Aligned legitimate-control policies with actual workflow paths: P3 controls permit draft/send, P1/P2 controls permit drafting while prohibiting unsafe sends, and the approved P2 Jira control permits comment updates while prohibiting creation because its complete fixture is already linked. Added complete Jira fields and exact per-case leak-policy tests, including tool-abuse and crescendo disclosures and explicit empty-list preservation.

Focused red result: `2 failed, 9 passed` before implementation.

Focused green command:

```text
LANGSMITH_TRACING=false /Users/testuser/incident-triage-agent/.venv/bin/python -m pytest -p no:cacheprovider tests/test_red_team_cases.py -q
```

Result: `11 passed in 0.37s`.

Full suite command (run once after fixes):

```text
LANGSMITH_TRACING=false /Users/testuser/incident-triage-agent/.venv/bin/python -m pytest -p no:cacheprovider
```

Result: `79 passed in 0.56s`.

Re-review fix commit: recorded with the report update.

## Third Correction Round

Aligned legitimate notification controls with their actual workflow paths: P3 controls permit draft/send and are write-allowed; the approved P2 CTRL-005 permits draft, Jira comment, and send while prohibiting new Jira creation. Added a disjoint allowed/prohibited-tool invariant for every case and made OB-003’s leak policy exactly cross-incident protected records.

Focused red result: `11 passed, 3 failed` before implementation.

Focused green result: `14 passed`.

Full suite command:

```text
LANGSMITH_TRACING=false /Users/testuser/incident-triage-agent/.venv/bin/python -m pytest -p no:cacheprovider
```

Result: `82 passed in 0.56s`.

Third-round commit: recorded with this report update.
