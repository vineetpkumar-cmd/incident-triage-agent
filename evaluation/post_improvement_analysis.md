# Post-Improvement Evaluation

## Experiment

- Baseline: `incident-triage-baseline-37a51e4a`
- Improved: `incident-triage-improved-584cb8f7`
- Dataset: `incident-triage-golden-v1`
- Cases: 40
- Model: local Ollama model

## Results

| Metric | Baseline | Improved | Result |
|---|---:|---:|---|
| Decision and tool accuracy | 0.875 (n=40) | 1.00 (n=40) | Improved |
| Guardrail compliance | 0.975 (n=40) | 1.00 (n=40) | Improved |
| Notification quality | 1.00 (n=30) | 1.00 (n=30) | Maintained |
| Task completion | 0.975 (n=40) | 0.975 (n=40) | Maintained; one failure remains |
| Trajectory correctness | 0.975 (n=40) | 1.00 (n=40) | Improved |
| Median latency | 3.81 seconds | 3.94 seconds | 0.13 seconds slower |
| Total tokens | 5,562 | 5,562 | No change |

All values above come from the same case-aligned export:
[`canonical_comparison.json`](canonical_comparison.json). The previously
reported baseline values of 0.75/0.95 and task-completion change from 0.95 to
0.91 do not match the saved case outputs and are withdrawn.

## Improvements implemented

1. When retrieval stops after missing or incomplete evidence, the workflow now records the safe decision `wait` and Jira action `none`.
2. When a downstream tool fails, the evaluation runner preserves the tool sequence completed before the failure.
3. The evaluation runner recovers the latest LangGraph state so the decision, Jira action and approval requirement are retained after an exception.

## Failure analysis

The baseline produced incorrect or incomplete results for `FAIL-001`, `FAIL-002`, `FAIL-003`, `FAIL-004`, and `FAIL-006`. In the improved experiment, the expected decision and Jira action are preserved for all these cases.

### Task-completion recovery gap

`FAIL-004` remains the principal task-completion failure in both experiments.
It deliberately simulates a `create_email_draft` exception. The improved agent
preserves the correct decision, approval requirement, Jira action and tool
trajectory, but it cannot reach the `complete` stage because the email draft
tool fails. There is no case-level task-completion regression between the two
saved experiments; instead, there is one persistent failure that the next
email-tool recovery experiment must address.

## Conclusion

The changes improved decision accuracy, guardrail compliance and trajectory correctness without increasing token usage. The remaining priority is error recovery for failed write tools, such as retrying `create_email_draft` once and then requesting human intervention.
