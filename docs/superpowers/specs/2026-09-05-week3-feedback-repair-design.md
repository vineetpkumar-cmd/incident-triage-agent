# Week 3 Incident Triage Feedback Repair Design

## Purpose

Address the Week 3 feedback by connecting Ollama to the LangGraph workflow, adding an agentic retrieval decision loop, documenting human review, updating the architecture diagram, and demonstrating the complete execution path.

## Current Problems

1. The submitted workflow prepares notification text using fixed Python text instead of calling the existing Ollama function.
2. ServiceNow and Jira retrieval runs only once before the workflow makes an operational decision.
3. The workflow does not assess whether the retrieved evidence is complete.
4. The architecture does not show a retrieval retry or human-assistance path.
5. A video demonstrating the complete workflow is missing.

## Architecture

The revised LangGraph workflow will:

1. Retrieve the ServiceNow incident.
2. Retrieve SLA information and related incidents.
3. Search for linked Jira issues.
4. Assess whether the retrieved evidence is complete and valid.
5. Retry retrieval once if the evidence is incomplete.
6. Pause and ask a human for help if the evidence remains incomplete.
7. Decide whether to wait, notify, or escalate when evidence is sufficient.
8. Use local Ollama to prepare the notification text.
9. Use a deterministic template if Ollama is unavailable.
10. Pause P1/P2 incidents for human approval.
11. Perform approved Jira and Outlook actions.
12. Finish with the workflow stage set to `complete`.

## Evidence Assessment

Deterministic Python rules will check the ServiceNow incident, SLA response, related-incident response, and Jira search response. Ollama will not decide whether operational evidence is safe or complete.

The evidence check will produce:

- `sufficient` when all required evidence is valid.
- `retry` when evidence is incomplete and no retry has occurred.
- `human_review` when evidence remains incomplete after one retry.

## Human Review

Human review is required in two situations:

1. When retrieval remains incomplete after one automatic retry, a human decides whether to retry again or stop. No Jira or Outlook changes are allowed while evidence is incomplete.
2. For P1/P2 incidents, a human must approve the proposed Jira and Outlook actions before they are executed.

P3 notifications may continue automatically because the mock tools still enforce recipient, project, issue-type, duplicate, and sending safety controls.

## Ollama Integration

The `prepare_notification` node will call the existing local Ollama email-generation function. The workflow will record whether the email came from `ollama` or `template_fallback`.

If Ollama is unavailable, the workflow will continue using a deterministic internal notification template. Operational decisions and approvals remain controlled by deterministic Python logic.

## State Changes

The LangGraph state will include:

- Evidence status
- Missing evidence fields
- Retrieval retry count
- Notification draft source
- Ollama error type, when applicable
- Human feedback
- Current workflow stage

## Error Handling

Missing or malformed retrieval results will not be passed to the decision node. The workflow will retry retrieval once and then ask for human help.

Tool errors must be recorded in the state rather than failing silently. Jira and Outlook writes must never occur after an unresolved retrieval failure or rejected approval.

## Testing

Automated tests will verify:

1. Complete evidence continues to triage.
2. Incomplete evidence triggers one retry.
3. Repeated incomplete evidence triggers human review.
4. No write action occurs with unresolved evidence.
5. Ollama is called for notification drafting.
6. Ollama failure activates the deterministic fallback.
7. P1/P2 actions require approval.
8. An approved end-to-end workflow reaches `complete`.

## Documentation and Video

The README architecture diagram will show the evidence decision, retry loop, Ollama drafting, retrieval human-review gate, and P1/P2 approval gate.

The demonstration video will show the architecture, a successful end-to-end incident, Ollama drafting, human approval, final Jira and Outlook results, the retrieval retry path, and the passing automated tests.