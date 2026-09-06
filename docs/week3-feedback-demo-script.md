# Week 3 Incident Triage Demonstration Script

## Preparation

Open three windows before recording:

1. The README architecture diagram in VS Code Markdown Preview.
2. The Streamlit application.
3. A terminal in the worktree directory.

Start Ollama in one terminal:

```bash
ollama serve
```

In another terminal:

```bash
cd /Users/testuser/incident-triage-agent/.worktrees/week4-evaluation
source /Users/testuser/incident-triage-agent/.venv/bin/activate
streamlit run streamlit_app.py
```

## Recording

### 1. Introduction — approximately 30 seconds

“This project is a fictional Incident Triage Agent built with LangChain, LangGraph, local Ollama, and mock MCP servers for ServiceNow, Jira, and Outlook.”

### 2. Architecture — approximately 45 seconds

Show the README diagram.

“The agent retrieves ServiceNow and Jira evidence, assesses whether it is sufficient, retries once when necessary, and asks a human if evidence remains incomplete. Once evidence is sufficient, it decides whether to wait, notify, or escalate. Ollama drafts the notification, while deterministic code controls safety and approval.”

### 3. Successful execution — approximately 2 minutes

Enter:

```text
INC0010001
```

Show:

- ServiceNow incident details
- Evidence status `Sufficient`
- Automatic retries `0`
- Triage decision
- Draft source `ollama`
- Outlook draft
- Human action-approval request

Say:

“The workflow has stopped before Jira modification and email sending because this is a P1 incident.”

Select **Approve**.

Show:

- Jira result
- Outlook send result
- Final stage `complete`

### 4. Retrieval loop — approximately 1 minute

Reset the application and enter:

```text
INC0099999
```

Show:

- Automatic retry count `1`
- Missing evidence
- Retrieval human-review request
- **Retry retrieval** and **Stop** choices

Select **Stop**.

Say:

“The agent attempted retrieval twice and then requested human assistance. It performed no Jira or Outlook write actions.”

### 5. Automated evidence — approximately 30 seconds

Run:

```bash
python -m pytest -q
```

Show the passing result.

Say:

“The automated tests cover retrieval assessment, retry routing, MCP failures, Ollama invocation and fallback, both human-review types, safety controls, and the complete approved execution path.”

## Final Statement

“This addresses the feedback by connecting Ollama to the active workflow, adding an agentic retrieval decision loop, documenting the architecture and human-review policy, and demonstrating the complete execution path.”