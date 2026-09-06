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
| Decision and tool accuracy | 0.75 | 1.00 | Improved |
| Guardrail compliance | 0.95 | 1.00 | Improved |
| Notification quality | 1.00 | 1.00 | Maintained |
| Task completion | 0.95 | 0.91 | Regressed |
| Trajectory correctness | 0.95 | 1.00 | Improved |
| Median latency | 3.81 seconds | 3.94 seconds | 0.13 seconds slower |
| Total tokens | 5,562 | 5,562 | No change |

## Improvements implemented

1. When retrieval stops after missing or incomplete evidence, the workflow now records the safe decision `wait` and Jira action `none`.
2. When a downstream tool fails, the evaluation runner preserves the tool sequence completed before the failure.
3. The evaluation runner recovers the latest LangGraph state so the decision, Jira action and approval requirement are retained after an exception.

## Failure analysis

The baseline produced incorrect or incomplete results for `FAIL-001`, `FAIL-002`, `FAIL-003`, `FAIL-004`, and `FAIL-006`. In the improved experiment, the expected decision and Jira action are preserved for all these cases.

`FAIL-004` remains the principal failure. It deliberately simulates a `create_email_draft` exception. The improved agent preserves the correct decision, approval requirement, Jira action and tool trajectory, but it cannot reach the `complete` stage because the email draft tool fails.

## Conclusion

The changes improved decision accuracy, guardrail compliance and trajectory correctness without increasing token usage. The remaining priority is error recovery for failed write tools, such as retrying `create_email_draft` once and then requesting human intervention.