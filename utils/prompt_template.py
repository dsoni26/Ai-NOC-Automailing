import os
import requests


def generate_incident_email(
    alert_title: str,
    server_name: str,
    severity: str,
    incident_description: str,
    actions_taken: str,
    recipient_email: str,
    next_update: str,
    suggested_steps: str,
    sop_context: list,
    similar_incidents: list,
    auto_draft: bool = True,
):
    subject = f"Incident Update: {alert_title or server_name}"
    sop_text = "\n\n".join([f"{doc.metadata.get('source', 'SOP')}:\n{doc.page_content}" for doc in sop_context]) if sop_context else "No matching SOP content available."

    similar_text = "\n\n".join([
        f"Title: {doc.metadata.get('title', 'Unknown')}\nSeverity: {doc.metadata.get('severity', 'Unknown')}\nStatus: {doc.metadata.get('status', 'Unknown')}\nDescription: {doc.metadata.get('description', '')}"
        for doc in similar_incidents
    ]) if similar_incidents else "No similar incidents found."

    suggested_text = suggested_steps.strip() or "Verify logs, restart impacted service, and confirm network connectivity."

    prompt = f"""
Please draft a professional NOC incident email for an enterprise operations team.

Incident Title: {alert_title}
Server Name: {server_name}
Severity: {severity}
Incident Description: {incident_description}
Actions Taken: {actions_taken}
Suggested FLT Steps: {suggested_text}
Next Update: {next_update}
Recipient Email: {recipient_email}

Include these sections:
- Incident Summary
- Current Status
- Actions Taken
- Severity Impact
- Troubleshooting Guidance
- Similar Incident Reference
- Next Update Plan

Add any relevant SOP context below:
{sop_text}

Include similar incident learnings:
{similar_text}

Use an enterprise professional tone and produce a well-structured email body.
"""

    if auto_draft:
        generated = call_ai_for_email(prompt)
        if generated:
            return generated.strip(), subject

    body = (
        f"Subject: {subject}\n\n"
        f"Hello Team,\n\n"
        f"Incident Summary:\n{incident_description}\n\n"
        f"Current Status:\nThe issue is currently being investigated on {server_name}. The incident is classified as {severity}.\n\n"
        f"Actions Taken:\n{actions_taken}\n\n"
        f"Suggested Field Troubleshooting Steps:\n{suggested_text}\n\n"
        f"Relevant SOP Context:\n{sop_text}\n\n"
        f"Similar Incident Reference:\n{similar_text}\n\n"
        f"Next Update:\n{next_update}\n\n"
        f"We will continue to monitor the situation and share an update at the next scheduled interval.\n\n"
        f"Regards,\nNOC Operations Team"
    )
    return body, subject


def call_ai_for_email(prompt: str) -> str:
    groq_key = os.getenv("GROQ_API_KEY")
    ollama_host = os.getenv("OLLAMA_HOST")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama2")

    if groq_key:
        try:
            response = requests.post(
                "https://api.groq.com/v1/complete",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "groq-wizard-1",
                    "prompt": prompt,
                    "max_output_tokens": 512,
                    "temperature": 0.2,
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("output", "") or data.get("choices", [{}])[0].get("text", "")
        except Exception:
            return ""

    if ollama_host:
        try:
            host = ollama_host.rstrip("/")
            endpoint = f"{host}/v1/chat/completions"
            response = requests.post(
                endpoint,
                json={
                    "model": ollama_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 512,
                    "temperature": 0.2,
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
        except Exception:
            return ""

    return ""
