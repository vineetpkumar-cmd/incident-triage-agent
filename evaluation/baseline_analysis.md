# Week 4 Baseline Evaluation

Experiment: incident-triage-baseline-37a51e4a  
Dataset: incident-triage-golden-v1  
Cases: 40

## Baseline metrics

| Metric | Result |
|---|---:|
| Decision and tool accuracy | 0.875 |
| Guardrail compliance | 0.975 |
| Notification quality | 1.00 on scored notifications |
| Task completion | 0.975 |
| Trajectory correctness | 0.975 |
| p50 latency | 3.81 seconds |
| p95 latency | 4.46 seconds |
| Total tokens | 5,562 |

## Failure analysis

### 1. Retrieval-stop state is incomplete

Cases FAIL-001, FAIL-002, FAIL-003 and FAIL-006 correctly stopped for human intervention, but returned no final decision or Jira action. The expected safe result is decision `wait` and Jira action `none`.

### 2. Tool exceptions lose partial workflow evidence

In FAIL-004, the Outlook draft tool raised an exception. The evaluation output lost the already-selected decision, planned Jira action, approval requirement and tool sequence.

### 3. Notification scoring is conditional

Cases that intentionally produce no notification receive `No feedback` for notification quality. This is expected because there is no email to judge and should not be counted as a quality failure.

## Proposed improvements

1. Set explicit safe output values when retrieval is stopped: decision `wait` and Jira action `none`.
2. Preserve partial state and tool-call evidence when a downstream tool fails.
3. Improve downstream tool-error handling so failures retain approval and diagnostic information.