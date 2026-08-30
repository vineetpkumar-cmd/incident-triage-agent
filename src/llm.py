import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama


load_dotenv()


async def generate_email_body(
    incident: dict,
    decision: str,
    jira_text: str,
) -> str:
    """Draft an incident email using a local Ollama model."""
    model_name = os.getenv(
        "OLLAMA_MODEL",
        "qwen3:4b",
    )

    model = ChatOllama(
        model=model_name,
        temperature=0,
    )

    prompt = f"""
/no_think

Write a concise internal incident notification email.

Use only the supplied facts. Do not invent information.
Return the email body only, without a subject line.

Incident number: {incident["number"]}
Priority: {incident["priority"]}
Description: {incident["description"]}
Assignment group: {incident["assignment_group"]}
Triage decision: {decision}
Jira information: {jira_text}
"""

    response = await model.ainvoke(prompt)
    body = str(response.content).strip()

    if not body:
        raise ValueError("Ollama returned an empty response.")

    return body