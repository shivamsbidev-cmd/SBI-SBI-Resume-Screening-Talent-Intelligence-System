Build a complete end-to-end Streamlit application called **SBI Resume Screening & Talent Intelligence System**.

## Objective

Create an AI-powered recruiter platform that can:

* Upload and process multiple PDF resumes
* Extract structured candidate information using LLMs
* Store candidate data in SQLite
* Create embeddings and semantic search using FAISS
* Rank candidates against Job Descriptions
* Provide RAG chatbot capabilities over resumes
* Generate talent intelligence analytics and reports
* Work with Cloud and Local LLMs

The system must be modular, production-ready, easy to explain during a capstone presentation, and avoid complex regex-based resume parsing.

---

# Tech Stack

Frontend:

* Streamlit

Database:

* SQLite3

Embeddings:

* sentence-transformers/all-MiniLM-L6-v2

Vector Store:

* FAISS

PDF Processing:

* PyPDF

Visualization:

* Plotly
* Pandas
* NumPy

AI Providers:

* OpenRouter
* Ollama
* Optional GPT4All

---

# Project Structure

Generate complete code for:

```text
app.py
database.py
resume_parser.py
llm_client.py
vector_store.py
semantic_search.py
candidate_ranker.py
rag_chat.py
analytics.py
utils.py
requirements.txt

data/
faiss_index/
uploads/
logs/
models/
```

Application must run using:

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

# LLM Provider Architecture

Create a unified LLM layer.

File:

```text
llm_client.py
```

Every AI feature must use this layer.

Functions:

```python
generate(prompt)

chat(messages)

extract_json(prompt)

summarize(text)
```

No module should directly call OpenRouter, Ollama, or GPT4All.

---

# Supported Providers

## OpenRouter

Load API key from environment variable:

```python
import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
```

Never hardcode API keys.

Supported models:

* openrouter/auto
* deepseek/deepseek-chat-v3-0324:free
* qwen/qwen3-32b:free
* anthropic/claude-sonnet-4
* openai/gpt-4.1-mini

---

## Ollama

Connect to:

```text
http://localhost:11434
```

Automatically detect installed models.

Support:

* qwen3
* llama3.2
* mistral
* gemma3
* phi4
* deepseek-r1

Allow model selection from Streamlit sidebar.

---

## GPT4All (Optional)

Support local GGUF models.

Detect models from:

```text
models/
```

Example:

* Phi-3-mini-4k-instruct.Q4_0.gguf
* Mistral-7B-Instruct.Q4_0.gguf
* Llama-3-8B-Instruct.Q4_0.gguf

Allow selection if available.

---

# Sidebar Controls

Create:

```text
LLM Provider
○ OpenRouter
○ Ollama
○ GPT4All

Model Selection

Upload Resumes

Build Index
```

---

# Database Design

Create SQLite database:

```text
data/sbi_talent.db
```

Table: candidates

Fields:

```text
id
name
email
phone
current_role
current_company
total_experience
education
skills
certifications
projects
summary
resume_text
upload_date
```

Table: rankings

```text
id
candidate_id
jd_text
score
created_at
```

Table: chat_history

```text
id
question
answer
timestamp
```

Automatically create tables.

Implement CRUD operations.

---

# Resume Upload Module

Allow:

* Single PDF Upload
* Bulk PDF Upload

Store original files in:

```text
uploads/
```

Display upload progress.

---

# AI Resume Parser

File:

```text
resume_parser.py
```

Avoid rule-based parsing.

Use LLM extraction.

Workflow:

1. Extract PDF text
2. Send resume text to selected LLM
3. Receive structured JSON
4. Validate JSON
5. Store in SQLite

Prompt:

You are an expert HR resume parser.

Extract candidate information and return ONLY valid JSON.

{
"name":"",
"email":"",
"phone":"",
"current_role":"",
"current_company":"",
"total_experience":"",
"education":"",
"skills":[],
"certifications":[],
"projects":[]
}

Rules:

* Return valid JSON only
* No markdown
* No explanations
* Use empty values when missing

---

# Fallback Extraction

If AI extraction fails:

Extract:

* Email
* Phone

using regex.

Store entire resume as raw text.

No resume should fail ingestion.

---

# Candidate Summary Generation

Generate AI summary:

Example:

"4-year experienced Data Analyst skilled in Python, SQL, Power BI and Banking Analytics."

Store summary in database.

Display in candidate profiles.

---

# Embedding Pipeline

File:

```text
vector_store.py
```

Use:

```text
all-MiniLM-L6-v2
```

Chunking:

```text
800 characters
100 overlap
```

Create embeddings.

Store vectors in FAISS.

Persist index:

```text
faiss_index/
```

Store metadata:

```text
candidate_id
candidate_name
chunk_text
```

---

# Semantic Search

File:

```text
semantic_search.py
```

Recruiters can search:

* Python Developer
* Banking Experience
* AWS Certification
* AI Engineer
* Data Analyst

Workflow:

1. Embed query
2. Search FAISS
3. Retrieve Top Candidates

Display:

* Name
* Experience
* Skills
* Summary
* Similarity Score

Top 10 results.

---

# Candidate Ranking

File:

```text
candidate_ranker.py
```

Input:

Job Description

Process:

* Embed JD
* Compare against candidate embeddings

Scoring:

70% Semantic Similarity

20% Skill Match

10% Experience Match

Formula:

Final Score =
(0.70 × Semantic Similarity)
+
(0.20 × Skill Match)
+
(0.10 × Experience Match)

Return Top 10 Candidates.

Generate AI explanation for every ranking.

Example:

"Strong match due to Python, SQL, Banking Analytics, AWS, and 5 years of relevant experience."

---

# RAG Resume Chatbot

File:

```text
rag_chat.py
```

Questions:

* Who has AWS certifications?
* Which candidates have Banking experience?
* Best Data Analyst candidates?
* Find Machine Learning Engineers.

Pipeline:

1. Embed question
2. Retrieve Top K chunks
3. Build context
4. Send to selected LLM
5. Generate response

Display source candidates.

Store chat history.

---

# Talent Intelligence Module

Generate:

* Top Skills
* Skill Gaps
* Talent Availability
* Certification Analysis
* Experience Distribution
* Hiring Recommendations

Generate AI Executive Summary.

Use selected LLM.

---

# Analytics Dashboard

File:

```text
analytics.py
```

KPIs:

* Total Candidates
* Average Experience
* Top Skill
* Top Certification

Charts:

* Skill Frequency
* Experience Distribution
* Education Distribution
* Candidate Ranking Scores

Use Plotly.

Interactive charts only.

---

# Candidate Profile Page

Display:

* Name
* Contact Details
* Current Role
* Current Company
* Experience
* Education
* Skills
* Certifications
* Projects
* AI Summary

Allow report export.

---

# Database Explorer

Features:

* View Candidates
* Search Candidates
* Filter by Skill
* Filter by Experience
* Filter by Education
* Delete Candidates

---

# Streamlit Navigation

Pages:

1. Dashboard
2. Upload Resumes
3. Candidate Database
4. Semantic Search
5. JD Ranking
6. Resume Chatbot
7. Talent Intelligence
8. Database Explorer

---

# Logging

Create:

```text
logs/app.log
```

Log:

* Upload Events
* Parsing Events
* Search Queries
* Ranking Requests
* Chat Interactions

---

# Error Handling

Handle gracefully:

* Invalid PDFs
* Empty PDFs
* Missing API Keys
* Ollama Not Running
* GPT4All Model Missing
* FAISS Errors
* SQLite Errors

Never crash the application.

Show user-friendly messages.

---

# Deliverable

Generate complete working code for every file.

The system should demonstrate:

* AI Resume Parsing
* SQLite Database Design
* Vector Search
* FAISS
* Semantic Retrieval
* RAG
* OpenRouter Integration
* Ollama Integration
* Optional GPT4All Integration
* Candidate Ranking
* Talent Intelligence Analytics

Code should be clean, modular, production-ready, and suitable for an SBI Capstone Project demonstration.
