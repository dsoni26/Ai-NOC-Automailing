import os
import json
import streamlit as st
from dotenv import load_dotenv
from utils.rag_pipeline import RAGPipeline
from utils.severity import classify_severity
from utils.mail_sender import send_email
from utils.prompt_template import generate_incident_email

load_dotenv()

st.set_page_config(
    page_title="AutoMailing Incident Assistant",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main {background-color: #0e1117;}
    .reportview-container .main {color: #d6d6d6;}
    .css-1d391kg {background-color: #0f172a;}
    .stButton>button {background-color: #106ba3; color: white;}
    .st-b6 {color: #d6d6d6;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AI-powered AutoMailing & Incident Assistant")
st.write("Enterprise-style incident email generation and Gmail SMTP dispatch for NOC teams.")

if "logs" not in st.session_state:
    st.session_state.logs = []
if "generated_email" not in st.session_state:
    st.session_state.generated_email = ""
if "email_subject" not in st.session_state:
    st.session_state.email_subject = ""

# RAG pipeline is built on launch and re-used
rag = RAGPipeline()

with st.sidebar:
    st.header("Settings")
    st.markdown("**AI & SMTP Configuration**")
    auto_draft = st.checkbox("Auto Draft Mode", value=True)
    approval_before_send = st.checkbox("Approval Before Send", value=True)
    st.markdown("---")
    st.markdown("**SMTP / API Config**")
    st.text_input("Gmail Email", value=os.getenv("GMAIL_EMAIL", ""), disabled=True)
    st.text_input("Gmail App Password", value="********" if os.getenv("GMAIL_APP_PASSWORD") else "Not set", disabled=True)
    st.text_input("Groq API Key", value="********" if os.getenv("GROQ_API_KEY") else "Not set", disabled=True)
    st.text_input("Ollama Host", value=os.getenv("OLLAMA_HOST", "http://localhost:11434"), disabled=True)
    st.markdown("---")
    st.header("Sample Incident History")
    if rag.incidents:
        for incident in rag.incidents[:3]:
            st.markdown(f"**{incident['incident_id']}** - {incident['title']}")
            st.text(f"{incident['date']} | Severity: {incident['severity']} | Status: {incident['status']}")
            st.write("---")
    else:
        st.write("No sample incidents loaded.")

col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Incident Inputs")
    alert_title = st.text_input("Alert Title", value="Server CPU spike causing degraded service")
    server_name = st.text_input("Server Name", value="web-frontend-03")
    severity_choice = st.selectbox("Severity", ["Auto Detect", "Critical", "High", "Medium", "Low"], index=0)
    incident_description = st.text_area("Incident Description", height=180, value="The application performance is degraded after repeated CPU spikes on the server. Users report slow page load times.")
    actions_taken = st.text_area("Actions Taken", height=120, value="Restarted the web service and cleared cached workers. Monitoring CPU after restart.")
    recipient_email = st.text_input("Recipient Email", value="noc-team@example.com")
    next_update = st.text_input("Next Update", value="We will provide the next update in 30 minutes.")
    suggested_steps = st.text_area("Suggested FLT Steps (comma-separated)", value="Restart service, verify logs, scale application pool, inspect network")

    if st.button("Generate Email"):
        derived_severity = severity_choice
        if severity_choice == "Auto Detect":
            derived_severity = classify_severity(f"{alert_title} {incident_description}")

        sop_hits = rag.retrieve_relevant_sop(incident_description)
        incident_hits = rag.retrieve_similar_incidents(incident_description)

        generated, subject = generate_incident_email(
            alert_title=alert_title,
            server_name=server_name,
            severity=derived_severity,
            incident_description=incident_description,
            actions_taken=actions_taken,
            recipient_email=recipient_email,
            next_update=next_update,
            suggested_steps=suggested_steps,
            sop_context=sop_hits,
            similar_incidents=incident_hits,
            auto_draft=auto_draft,
        )
        st.session_state.generated_email = generated
        st.session_state.email_subject = subject
        st.session_state.logs.append("Email draft generated.")
        st.success("Generated incident email draft.")

    if st.button("Send Email"):
        if not st.session_state.generated_email:
            st.error("Generate an email before sending.")
        elif approval_before_send:
            if st.checkbox("I approve sending this email", key="approval_checkbox"):
                success, message = send_email(
                    subject=st.session_state.email_subject or f"Incident Update: {alert_title}",
                    body=st.session_state.generated_email,
                    recipient=recipient_email,
                )
                st.session_state.logs.append(message)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.warning("Check approval before sending.")
        else:
            success, message = send_email(
                subject=st.session_state.email_subject or f"Incident Update: {alert_title}",
                body=st.session_state.generated_email,
                recipient=recipient_email,
            )
            st.session_state.logs.append(message)
            if success:
                st.success(message)
            else:
                st.error(message)

with col2:
    st.subheader("Generated Email Preview")
    if st.session_state.generated_email:
        st.text_area("Email Content", value=st.session_state.generated_email, height=520)
    else:
        st.info("Generate an incident email draft to preview it here.")

    st.markdown("---")
    st.subheader("Email Summary")
    st.metric("Severity", classify_severity(f"{alert_title} {incident_description}") if severity_choice == "Auto Detect" else severity_choice)
    st.metric("Target Recipient", recipient_email or "Not set")
    st.metric("Auto Draft Mode", "Enabled" if auto_draft else "Disabled")
    st.metric("Approval Required", "Yes" if approval_before_send else "No")

with st.expander("Logs & Diagnostics", expanded=True):
    for entry in st.session_state.logs[-10:]:
        st.write(f"- {entry}")

with st.expander("Sample Incident History Viewer", expanded=False):
    if rag.incidents:
        for idx, incident in enumerate(rag.incidents, start=1):
            st.markdown(f"### {idx}. {incident['title']}")
            st.write(f"**Severity:** {incident['severity']}  |  **Status:** {incident['status']}  |  **Date:** {incident['date']}")
            st.write(f"**Description:** {incident['description']}")
            st.write(f"**Actions Taken:** {incident['actions_taken']}")
            st.write("---")
    else:
        st.write("No historical incidents available.")

with st.expander("Retrieved SOP Context", expanded=False):
    sop_hits = rag.retrieve_relevant_sop(incident_description)
    if sop_hits:
        for idx, doc in enumerate(sop_hits, start=1):
            st.markdown(f"**SOP {idx}: {doc.metadata.get('source', 'unknown')}**")
            st.write(doc.page_content[:400] + ("..." if len(doc.page_content) > 400 else ""))
            st.write("---")
    else:
        st.write("No relevant SOP content found.")
