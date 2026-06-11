# SBI Resume Screening & Talent Intelligence System

## Project Overview

SBI Resume Screening & Talent Intelligence System is a complete Streamlit-based HR platform for resume ingestion, PDF parsing, semantic search, RAG chat, candidate ranking, analytics, and talent intelligence reporting.

Recruiters can upload multiple PDF resumes, extract structured candidate data, store it in SQLite, create embeddings with Sentence Transformers, store content in FAISS, and perform search and ranking workflows with OpenRouter-powered generation.

## Features

- Bulk PDF resume upload and parsing
- Structured extraction of name, email, phone, skills, experience, education, certifications, projects, current role, and current company
- SQLite persistence for resumes, skills, certifications, projects, rankings, and chat history
- FAISS vector index for semantic candidate search
- RAG chatbot over all uploaded resumes using OpenRouter
- Job description candidate ranking with semantic similarity, skill match, experience match, and education match
- Talent intelligence report generation
- Responsive Streamlit dashboard with Plotly visualization
- Export Excel and PDF reports
- Database explorer for recruiters

## Architecture

- `app.py` - Streamlit frontend and page orchestration
- `database.py` - SQLite setup, CRUD operations, transaction handling
- `resume_parser_2.py` - PDF text extraction and resume metadata parsing
- `rag_engine.py` - Embeddings, FAISS index management, document retrieval, chat prompt assembly
- `candidate_ranker.py` - JD/resume scoring and ranking logic
- `talent_intelligence.py` - intelligence report generation
- `analytics.py` - dashboard metric preparation and Plotly charts
- `utils.py` - logging, file helpers, OpenRouter client utilities

## Installation

1. Clone the repository or open this workspace.
2. Create a Python 3.10+ virtual environment.
3. Install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## OpenRouter Setup

1. Sign up at [OpenRouter](https://openrouter.ai).
2. Generate an API key.
3. Use the API key in the sidebar when launching Streamlit.
4. Supported models:
   - `openrouter/auto`
   - `deepseek/deepseek-chat-v3-0324:free`
   - `qwen/qwen3-32b:free`
   - `anthropic/claude-sonnet-4`
   - `openai/gpt-4.1-mini`

## Database Design

The system creates a persistent SQLite database at `data/sbi_talent_intelligence.db` with tables:

- `resumes`
- `skills`
- `certifications`
- `projects`
- `candidate_scores`
- `chat_history`

## RAG Pipeline

1. Upload PDF resumes
2. Extract text from resume pages
3. Chunk text into 800-token segments with 100-token overlap
4. Create embeddings using `all-MiniLM-L6-v2`
5. Store vectors in FAISS
6. Retrieve top segments for a query
7. Answer questions with OpenRouter LLM

## Running Streamlit

```bash
streamlit run app.py
```

Open the local URL shown in the terminal.

## Example Queries

- "Find Python developers with 3+ years experience"
- "Show candidates with AWS certifications"
- "Who has Banking and AI experience?"
- "Who is best suited for Data Analyst role?"

## Deployment Guide

### Local Execution

- Install dependencies
- Run `streamlit run app.py`
- Provide your OpenRouter API key in the sidebar

### Streamlit Cloud

- Push the repository to GitHub
- Connect the repo to Streamlit Cloud
- Set a secret for `OPENROUTER_API_KEY` or provide it from the app UI
- Configure `requirements.txt`

### Docker Deployment

Create a simple Dockerfile and mount `data/` and `faiss_index/` for persistence.

## Future Enhancements

- Azure/Google Cloud storage support
- Multi-user access and authentication
- Enhanced duplicate detection with checksum and fuzzy similarity
- Advanced resume clustering and candidate personas
- Interview question generation via OpenRouter
- PDF report templates and scheduled export
- Scheduled analytics and alerts

## Notes

- Resume data persists across sessions in `data/sbi_talent_intelligence.db`.
- FAISS index files are stored in `faiss_index/`.
- Keep OpenRouter API key private and stored securely.
