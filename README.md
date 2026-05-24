# AI AutoMailing & Incident Assistant

This project is a Streamlit-based NOC assistant for generating professional incident emails, retrieving SOP context, and sending messages via Gmail SMTP.

## Features

- Streamlit enterprise dashboard with dark/light design
- Incident email generation using Groq or Ollama AI
- Gmail SMTP integration using App Password authentication
- Severity classification (Critical / High / Medium / Low)
- Local RAG with SOP retrieval using LangChain, SentenceTransformers, and FAISS
- Semantic similarity search for historical incidents
- Auto Draft Mode and Approval Before Send toggles
- Incident history viewer and diagnostics logs
- Docker support with `Dockerfile` and `docker-compose.yml`

## Folder Structure

```
project/
│
├── app.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── docs/
├── historical_incidents/
└── utils/
    ├── rag_pipeline.py
    ├── mail_sender.py
    ├── severity.py
    └── prompt_template.py
```

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and add your credentials.

3. Run the app:

```bash
streamlit run app.py
```

## Optional: Docker

Build and run with Docker:

```bash
docker compose build
docker compose up
```

## How RAG Works in This Project

- Local SOP files are loaded from `docs/`
- Sentence embeddings are generated with `SentenceTransformerEmbeddings`
- FAISS stores the embeddings and performs vector similarity search
- When an alert is provided, the app retrieves the most relevant SOP entries and includes that context in the email draft

## How Gmail SMTP Works

- Gmail SMTP connects to `smtp.gmail.com` using SSL on port `465`
- The app uses the credentials from `.env`
- Gmail App Password authentication is required for SMTP access

## Embeddings and Semantic Similarity

- The app converts text into dense vectors using a sentence-transformer model
- Similarity is computed by comparing vectors in FAISS
- This enables retrieval of relevant SOP documents and similar historical incidents based on alert text

## Notes

- If `GROQ_API_KEY` is configured, the app will attempt Groq completion
- If `OLLAMA_HOST` is configured, the app will attempt Ollama local generation
- If no AI endpoint is reachable, the app falls back to a structured draft template
