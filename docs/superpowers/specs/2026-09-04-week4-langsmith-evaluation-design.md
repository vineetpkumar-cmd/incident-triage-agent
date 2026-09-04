# Week 4 LangSmith Evaluation Design

## Purpose

Extend the Week 3 Incident Triage Agent with a repeatable evaluation system. The existing LangGraph agent remains the system under test; Week 4 adds tracing, a golden dataset, evaluators, failure analysis, and baseline-versus-improved comparison.

## Evaluation One-Liner

I will measure task completion, decision and tool accuracy, guardrail compliance, notification quality, and latency on the Week 3 Incident Triage Agent using a golden dataset of 40 fictional cases covering happy paths, edge cases, known failures, and adversarial inputs. Code-based and trajectory evaluators will score deterministic behaviour, local Ollama will judge notification quality, and a small human-reviewed sample will calibrate the judge; the baseline and post-improvement experiments will be traced and compared in LangSmith.

## Agent and User Outcome

The agent under test is the stateful LangGraph Incident Triage Agent backed by local Ollama and fictional ServiceNow, Jira, and Outlook MCP servers. A successful run retrieves and enriches an incident, chooses the correct response, takes only permitted Jira and Outlook actions, and requests human approval at the correct point.

## Scope

Evaluation covers the complete workflow and its intermediate trajectory:

1. Retrieve the fictional ServiceNow incident.
2. Retrieve SLA evidence and related incidents.
3. Search Jira for linked engineering work.
4. Decide whether to wait, notify, or escalate.
5. Generate an Outlook notification using local Ollama, falling back to a deterministic factual template if the local model fails.
6. Pause for human approval when policy requires it.
7. Create or update a fictional Jira issue when appropriate.
8. Draft and send the approved fictional Outlook notification.

Each case runs against isolated temporary copies of the mock JSON databases. Evaluation must not change the repository's original demo data.

## Baseline Prerequisite

Repository review found that `src/llm.py` defines the intended local Ollama notification generator, but `prepare_notification` currently constructs only a deterministic Python template and does not call it. Before freezing the Week 4 baseline, connect `generate_email_body()` to `prepare_notification`, retain the deterministic template as an explicit fallback for model failure, and add tests for both paths. The resulting tested version is the baseline agent because it restores the Week 3 architecture that the project claims to evaluate; no evaluation-driven improvements are applied until after baseline results exist.

## Metrics and Pass Bars

### Task Completion Rate

A code-based evaluator checks that the predicted final stage and required actions match the reference behaviour. Pass bar: at least 85% of cases.

### Decision and Tool Accuracy

Code-based and trajectory evaluators check the wait/notify/escalate decision, Jira action, email action, tool selection, and required tool ordering. Pass bar: at least 90%.

### Guardrail Compliance

A code-based evaluator checks approval enforcement, allowed recipients, duplicate prevention, prohibited actions, and adversarial-input handling. Pass bar: 100%; any unsafe write is a critical failure.

### Notification Quality

A local Ollama evaluator scores factuality against the incident evidence, clarity, professional tone, and structural completeness using a fixed rubric. A small human-reviewed sample calibrates the rubric before the full run. Pass bar: at least 80%.

### Latency and Tool Calls

The runner records total duration, node duration where available, and tool-call count. The baseline establishes p50 and p95 latency; the improved run must not increase p95 latency by more than 10% unless a documented quality or safety improvement justifies the trade-off.

## Golden Dataset

The official LangSmith dataset is named `incident-triage-golden-v1`. A local, version-controlled JSON source contains only fictional data and enables review and reproducibility.

The 40 cases use this fixed scenario mix:

- 20 happy-path cases (50%)
- 12 edge cases (30%)
- 6 known-failure cases (15%)
- 2 adversarial cases (5%)

Every case contains:

- `case_id`
- fictional incident input or fixture
- `scenario_type` and `difficulty`
- expected decision
- expected Jira action
- expected approval requirement and simulated response
- expected email action
- expected final stage
- expected tool sequence
- safety expectations
- short reference rationale

Every expected result is reviewed manually before upload. The dataset remains unchanged between baseline and improved experiments so the measured delta is comparable.

## Architecture

The new `evaluation` package surrounds, but does not duplicate, the existing application:

```text
LangSmith golden dataset
          |
          v
Evaluation runner --> isolated temporary mock-data workspace
          |
          v
Existing LangGraph Incident Triage Agent
          |
          +-- ServiceNow mock MCP calls
          +-- Jira mock MCP calls
          +-- Ollama notification generation
          +-- simulated human approval
          +-- Outlook mock MCP calls
          |
          v
Predicted result + intermediate trajectory
          |
          +-- code-based evaluators
          +-- trajectory evaluator
          +-- local Ollama quality judge
          +-- latency/tool-call measurements
          |
          v
LangSmith baseline and improved experiments
```

Proposed files:

```text
evaluation/
├── golden_cases.json
├── dataset.py
├── runner.py
├── evaluators.py
├── ollama_judge.py
└── reports.py

tests/
├── test_dataset.py
├── test_evaluation_runner.py
└── test_evaluators.py
```

## Trace Design

Each dataset example produces one parent trace. LangGraph nodes, Ollama invocations, and MCP tool calls appear as child runs. Stable trace metadata includes:

- case ID
- scenario type and difficulty
- run name
- experiment name
- agent version
- prompt version
- dataset version
- expected and predicted decision
- expected and predicted final stage
- correctness indicators
- error category

Secrets never appear in trace inputs, outputs, tags, or metadata. Only fictional incidents are evaluated and uploaded.

## Evaluation Runner

For each LangSmith example, the runner:

1. Validates the case schema.
2. Creates an isolated temporary data workspace.
3. Seeds ServiceNow, Jira, and Outlook fixtures for that case.
4. Invokes the existing LangGraph workflow with a unique thread ID.
5. Simulates the labelled approval or rejection response if interrupted.
6. Captures the final state, ordered trajectory, timing, and errors.
7. Returns a stable prediction schema for evaluators.
8. Cleans up temporary data even when the case fails.

One failed case is returned as a scored failure and does not terminate the remaining experiment.

## Evaluators

Code-based evaluators remain deterministic and independently testable. They return named scores and concise failure explanations for task completion, decision accuracy, action accuracy, approval compliance, safety compliance, and trajectory correctness.

The Ollama judge receives only the fictional source evidence, generated notification, and fixed rubric. It returns structured scores for factuality, clarity, tone, and completeness. If the judge fails or returns invalid output, the evaluation records a missing judge score and an error rather than inventing a value.

Human review covers a small calibration sample containing at least one happy path, one edge case, one known failure, one adversarial case, and both P1 and P2 approval paths. Material disagreement with Ollama triggers rubric refinement before the baseline experiment.

## Baseline and Improvement Process

1. Upload and version the reviewed golden dataset.
2. Verify one end-to-end trace and all expected child runs.
3. Run four representative smoke cases.
4. Run the unchanged Week 3 agent as the baseline experiment.
5. Rank failure modes by frequency and severity and retain a representative trace for each of the top three.
6. Select three or four targeted improvements based on baseline evidence.
7. Implement and test those changes.
8. Run the same dataset as the improved experiment with the same trace and metadata schema.
9. Report absolute scores, per-metric delta, regressions, latency impact, remaining failures, and next actions.

Potential improvement categories include prompt clarity, tool input validation, explicit error recovery, bounded retry behaviour, output schema validation, and control-flow verification. No improvement is selected solely on assumption; the baseline evidence determines the final changes.

## Error Handling

- Dataset validation fails before an experiment begins if a label is missing or contradictory.
- A case-level timeout prevents stalled model or tool calls from blocking the suite.
- Tool and model exceptions are captured with a stable error category.
- Temporary data cleanup occurs in a `finally` path.
- Ollama-judge failure does not erase deterministic evaluator results.
- LangSmith upload or tracing failure is reported explicitly; the runner does not claim that an untraced run satisfied the handout.

## Testing Strategy

The existing 18 tests must continue to pass. New tests cover dataset schema validation, case isolation, approval simulation, prediction schema stability, each deterministic evaluator, trajectory scoring, error recording, cleanup, and invalid Ollama-judge output.

Execution increases gradually: unit tests, one traced case, four representative cases, then all 40 cases. Baseline and improved experiments use identical dataset version, evaluator versions, trace hierarchy, and metadata fields.

## Deliverables

- Completed evaluation-framework table and one-line evaluation statement
- `incident-triage-golden-v1` LangSmith dataset with 40 labelled cases
- Baseline LangSmith experiment link and verified trace
- Metric summary and top-three failure analysis
- Three or four evidence-based improvements
- Improved LangSmith experiment link
- Baseline-versus-improved comparison with per-metric deltas
- Production-monitoring proposal for quality drift, latency, guardrail trips, and tool failures
- Updated repository documentation and reproducible commands

## Out of Scope

- Building a new agent
- Connecting to real ServiceNow, Jira, or Outlook accounts
- Uploading real incidents or personal information
- Replacing local Ollama with a paid model solely for evaluation
- Production deployment or persistent production monitoring
