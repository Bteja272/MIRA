# 🩺 MIRA
### Medical Intelligence and Retrieval Assistant

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?style=flat&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-Frontend-646CFF?style=flat&logo=vite&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Orchestration-FF6B6B?style=flat)
![LangChain](https://img.shields.io/badge/LangChain-Retrieval-1C3C3C?style=flat)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=flat&logo=postgresql&logoColor=white)
![Ollama](https://img.shields.io/badge/LLM-Ollama_%7C_llama3.2-black?style=flat)
![Tavily](https://img.shields.io/badge/Search-Tavily-blue?style=flat)
![Alembic](https://img.shields.io/badge/Migrations-Alembic-orange?style=flat)
![Docker](https://img.shields.io/badge/Docker-PostgreSQL-2496ED?style=flat&logo=docker&logoColor=white)
![Vitest](https://img.shields.io/badge/Vitest-19%2F19_Passing-6E9F18?style=flat&logo=vitest&logoColor=white)
![Cypress](https://img.shields.io/badge/Cypress-2%2F2_E2E_Passing-17202C?style=flat&logo=cypress&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active_Development-yellow?style=flat)

> You upload your medical document. You ask: **"What medications and follow-up instructions are documented here?"** MIRA retrieves the relevant evidence from your selected record, explains it in plain English, cites the source, and appends a deterministic medical disclaimer — without diagnosing you or recommending treatment changes.

---

## What MIRA Is

MIRA is a **safety-first medical document intelligence platform** for understanding personal medical records.

It combines authenticated document ownership, retrieval-augmented generation, structured medical extraction, deterministic safety checks, and a full React interface.

The critical distinction:

> **MIRA explains what your documents say. It does not make new medical determinations.**

**What MIRA does:**

- Register and authenticate users
- Keep each user's documents isolated
- Upload and index PDF or TXT medical records
- Summarize discharge summaries, lab reports, prescriptions, imaging reports, and visit notes
- Answer grounded questions using one or more selected documents
- Compare multiple documents while preserving source boundaries
- Explain medical terminology found in uploaded records
- Search current public medical information through Tavily
- Extract structured medical facts with supporting evidence
- Permanently delete documents, chunks, embeddings, and extraction records
- Present all major workflows through a React and TypeScript frontend

**What MIRA never does:**

- Diagnose conditions based on symptoms
- Recommend changing, stopping, or adjusting medication
- Predict outcomes or prognosis
- Treat generated text as a substitute for a licensed professional
- Allow one user to access another user's records
- Skip the medical disclaimer on health-related responses

---

## Current User Experience

MIRA now includes a complete authenticated web application.

### Frontend workflows

- **Registration and login**
- **Protected routes**
- **Document upload with validation and progress**
- **Duplicate-upload detection**
- **Document library and permanent deletion**
- **Multi-document selection**
- **Grounded Q&A with source cards**
- **Current-information answers with web sources**
- **Structured medical extraction**
- **Evidence review for extracted facts**
- **Stored extraction deletion**
- **Session-expiration handling**
- **Offline and network-status feedback**
- **Mobile navigation**
- **Accessible forms, focus handling, and skip navigation**
- **Global error boundary**

### Main frontend routes

| Route | Purpose |
|---|---|
| `/register` | Create an account |
| `/login` | Authenticate |
| `/` | Dashboard |
| `/documents` | Upload, review, refresh, and delete documents |
| `/ask` | Ask direct, document-grounded, or current-information questions |
| `/extractions` | Generate and review structured medical facts |

---

## Safety Architecture

Medical-risk queries are blocked **before** the LangGraph agent, before retrieval, and before any LLM call.

This is deterministic application logic — not a language model making its own safety decision.

```text
User Query
     ↓
Deterministic Safety Guard
     │
     ├── Emergency keyword detected   → Immediate emergency guidance
     ├── Self-harm indicator          → Crisis-oriented response
     ├── Symptom diagnosis request    → Redirect to a healthcare provider
     ├── Prognosis request            → Decline to predict an outcome
     └── Medication-change request    → Refuse medication-change guidance
     
Allowed Query
     ↓
LangGraph Router
     │
     ├── Selected document IDs       → RAG pipeline using pgvector
     ├── Multi-document comparison   → Complete retrieval for all selected docs
     ├── Explicit latest/current     → Tavily web search
     └── General knowledge           → Direct Ollama LLM
     ↓
Deterministic disclaimer appended by application code
     ↓
Source-cited response
```

The disclaimer is **never generated conditionally by the LLM**. It is appended by the application layer.

---

## Authentication and Data Isolation

MIRA now supports authenticated multi-user development workflows.

**Implemented controls:**

- Email and password registration
- Argon2 password hashing
- JWT access tokens
- Protected backend routes
- Protected frontend routes
- Per-user document ownership
- Per-user duplicate detection
- Authorization checks for querying, extraction, and deletion
- Cross-user access prevention
- React Query cache clearing between users
- Automatic logout after an invalid or expired session

The frontend currently stores the access token in `sessionStorage` as an MVP implementation.

A production deployment should move to secure HTTP-only cookies, CSRF protection, stricter session management, encryption, and audit logging.

---

## What Makes This Different From Generic RAG

Most RAG systems retrieve similar chunks and pass them to a model. For medical documents, this is not enough.

| Problem | How MIRA handles it |
|---|---|
| Similarity search omits sections | Summaries use **complete-document retrieval** |
| Multi-document facts become mixed | Document **boundaries are preserved** throughout the prompt |
| Model classifies lab values | Only the laboratory's **documented flag** is reproduced |
| LLM could skip the disclaimer | Disclaimer is appended **deterministically by code** |
| Emergency requests reach the LLM | A **pre-routing safety guard** blocks them first |
| Duplicate files pollute retrieval | **SHA-256 detection** rejects exact duplicates |
| Users can access each other's files | **Ownership checks** protect every document operation |
| Lines split across chunks | **Newline-aware chunking** preserves medical line structure |
| Schema changes drift | **Alembic migrations** manage versioned database changes |
| Extraction output cannot be reviewed | Facts include **supporting evidence and source metadata** |
| Frontend state leaks between users | Query caches are cleared on authentication changes |

---

## Routing Table

| User request | Route | Why |
|---|---|---|
| "Summarize this uploaded report" | Full-document RAG | Similarity search alone may omit sections |
| "What medications are documented here?" | Selected-document RAG | The answer must be grounded in the selected source |
| "Compare these two lab reports" | Multi-document RAG | Retrieves complete content and preserves boundaries |
| "What does HbA1c mean?" | Direct LLM | General knowledge does not require a document |
| "What are the latest public guidelines?" | Tavily web search | The request explicitly requires current information |
| "Should I stop taking this medication?" | Safety guard | Medication-change guidance is blocked |
| "I have chest pain right now" | Safety guard | Emergency guidance occurs before retrieval |

---

## Example Response — Grounded Medical Document Question

**Query:**

```json
{
  "query": "What medications and follow-up instructions are documented?",
  "document_id": "DOCUMENT_ID"
}
```

**MIRA response, summarized:**

```text
Based on synthetic_discharge_summary.txt:

Medication
  Lisinopril 10 mg once daily

Follow-up
  Follow up with the primary care physician within 7 days.

[Source: synthetic_discharge_summary.txt · discharge_summary · chunk 1]

---
MEDICAL NOTICE: This information explains what is documented in your
uploaded medical record. It is not medical advice, diagnosis, or
treatment guidance. Consult a qualified healthcare provider for decisions.
```

The model is instructed to remain grounded in the selected document and not invent undocumented medical facts.

---

## Multi-Document Comparison

```json
{
  "query": "Compare these two reports and identify documented changes.",
  "document_ids": [
    "DOCUMENT_ID_1",
    "DOCUMENT_ID_2"
  ]
}
```

MIRA:

1. Confirms every document belongs to the authenticated user
2. Rejects missing or unauthorized document IDs
3. Retrieves the complete indexed content of every selected document
4. Preserves filenames and document boundaries
5. Produces source-specific summaries
6. Identifies only explicitly documented differences
7. Avoids unsupported clinical inference
8. Labels evidence with filename, type, document ID, and chunk location

Current local limit: **5 documents per request**.

---

## Structured Medical Extraction

MIRA can transform an uploaded document into a persisted structured representation.

**Current extraction categories include:**

- Patient information
- Diagnoses
- Medications
- Allergies
- Procedures
- Follow-up instructions
- Additional document facts supported by the extraction schema

Each extracted fact may include:

- Normalized value
- Supporting evidence
- Source filename
- Document ID
- Page or chunk position

```text
Owned Document
     ↓
Complete indexed document retrieval
     ↓
Medical extraction prompt
     ↓
Structured JSON validation
     ↓
Persisted extraction record
     ↓
Evidence-backed frontend presentation
```

Structured extraction is intended for document understanding, not autonomous clinical decision-making.

---

## Document Ingestion Pipeline

```text
Authenticated PDF / TXT Upload
     ↓
Filename and extension validation
     ↓
25 MB upload size limit
     ↓
UUID-based stored filename
     ↓
SHA-256 duplicate detection
     ↓
Text extraction using pypdf
     ↓
Line-preserving text cleaning
     ↓
Newline-aware overlapping chunking
     ↓
Medical document classification
     ↓
SentenceTransformers all-MiniLM-L6-v2 embeddings
     ↓
PostgreSQL + pgvector · HNSW cosine index
```

**Supported document types:**

`lab_report` · `discharge_summary` · `prescription` · `imaging_report` · `pathology_report` · `visit_note` · `vaccination_record` · `insurance_document` · `unknown`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Routing | React Router |
| Server-state management | TanStack Query |
| API client | Native Fetch API |
| Authentication state | React Context |
| Styling | Plain CSS |
| Backend API | FastAPI |
| Authentication | JWT, Argon2 |
| Agent orchestration | LangGraph |
| Retrieval abstraction | LangChain-compatible retriever |
| Embeddings | SentenceTransformers `all-MiniLM-L6-v2` |
| Vector database | PostgreSQL + pgvector |
| Vector index | HNSW cosine |
| ORM | SQLAlchemy |
| Schema migrations | Alembic |
| Local LLM | Ollama · llama3.2 |
| Web search | Tavily |
| Document parsing | pypdf |
| Database container | Docker Compose |
| Frontend testing | Vitest, Testing Library |
| End-to-end testing | Cypress |
| Backend testing | Pytest / unittest-based suite |
| Development environment | WSL2, Linux, Docker |

---

## 🏗️ Key Technical Decisions

**Why deterministic safety before LangGraph routing?**  
Medical-risk classification should not depend on a language model correctly identifying an emergency, diagnosis request, prognosis request, or medication-change request.

**Why complete-document retrieval for summaries?**  
A generic summary query may not semantically match every section of a medical report. Complete retrieval reduces omission risk.

**Why preserve document boundaries in multi-document prompts?**  
Without explicit boundaries, a model may associate a medication, diagnosis, date, or lab value with the wrong document.

**Why forbid independent lab-value classification?**  
The model does not have the full clinical context needed to label a value. MIRA reproduces the laboratory's documented flag instead.

**Why use line-preserving cleaning and newline-aware chunking?**  
Medical records often place the test name, result, unit, reference range, and flag on adjacent lines. Preserving line structure keeps related information together.

**Why use SHA-256 duplicate detection?**  
Repeated ingestion creates duplicate vectors and can distort retrieval. Hash comparison rejects identical files before unnecessary processing.

**Why use Alembic instead of `Base.metadata.create_all()`?**  
Alembic tracks controlled schema changes for users, ownership, extraction records, and future production features.

**Why Ollama locally?**  
Ollama provides local inference, no per-request development cost, and no external LLM dependency during synthetic-data development.

**Why React Query?**  
The frontend must coordinate authenticated uploads, document lists, deletions, extraction state, and query results. React Query provides caching, invalidation, loading states, and user-specific cache control.

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Bteja272/MIRA.git
cd MIRA
```

### 2. Create the backend environment

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure backend environment variables

```bash
cp .env.example .env
```

Configure the required local values:

```env
DATABASE_URL=postgresql+psycopg://...
TAVILY_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Do not commit `.env`.

### 4. Start PostgreSQL and pgvector

```bash
docker compose up -d
docker compose ps
```

### 5. Apply database migrations

```bash
python -m alembic -c alembic.ini upgrade head
```

### 6. Start Ollama

```bash
ollama pull llama3.2
ollama serve
```

Verify:

```bash
curl http://localhost:11434/api/tags
```

### 7. Start the backend

```bash
python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8001 \
  --reload
```

API: `http://127.0.0.1:8001`  
Docs: `http://127.0.0.1:8001/docs`

### 8. Install frontend dependencies

Open another terminal:

```bash
cd frontend
npm ci
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8001
```

### 9. Start the frontend

```bash
npm run dev
```

Frontend: `http://127.0.0.1:5173`

Production preview:

```bash
npm run build
npm run preview
```

Preview: `http://127.0.0.1:4173`

---

## 🔌 API Reference

Base URL:

```text
http://127.0.0.1:8001
```

### Register

```bash
curl -X POST http://127.0.0.1:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "synthetic.user@example.com",
    "password": "SyntheticPassword!2026"
  }'
```

### Login

```bash
curl -X POST http://127.0.0.1:8001/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=synthetic.user@example.com&password=SyntheticPassword!2026"
```

Save the returned token:

```bash
export MIRA_TOKEN="YOUR_ACCESS_TOKEN"
```

### Current user

```bash
curl http://127.0.0.1:8001/auth/me \
  -H "Authorization: Bearer $MIRA_TOKEN"
```

### Ingest a document

```bash
curl -X POST http://127.0.0.1:8001/ingest \
  -H "Authorization: Bearer $MIRA_TOKEN" \
  -F "file=@sample_data/synthetic_lab_report.txt"
```

```json
{
  "duplicate": false,
  "document_id": "4fe8c6d0-...",
  "filename": "synthetic_lab_report.txt",
  "document_type": "lab_report",
  "chunks_indexed": 2,
  "message": "Document indexed successfully"
}
```

### List owned documents

```bash
curl http://127.0.0.1:8001/documents \
  -H "Authorization: Bearer $MIRA_TOKEN"
```

### Query one document

```bash
curl -X POST http://127.0.0.1:8001/query \
  -H "Authorization: Bearer $MIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize this document.",
    "document_id": "DOCUMENT_ID"
  }'
```

### Compare multiple documents

```bash
curl -X POST http://127.0.0.1:8001/query \
  -H "Authorization: Bearer $MIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare these and identify documented differences.",
    "document_ids": [
      "DOCUMENT_ID_1",
      "DOCUMENT_ID_2"
    ]
  }'
```

### Generate structured extraction

```bash
curl -X POST \
  http://127.0.0.1:8001/documents/DOCUMENT_ID/extract \
  -H "Authorization: Bearer $MIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "replace_existing": false
  }'
```

### Read structured extraction

```bash
curl \
  http://127.0.0.1:8001/documents/DOCUMENT_ID/extraction \
  -H "Authorization: Bearer $MIRA_TOKEN"
```

### Delete structured extraction

```bash
curl -X DELETE \
  http://127.0.0.1:8001/documents/DOCUMENT_ID/extraction \
  -H "Authorization: Bearer $MIRA_TOKEN"
```

### Permanently delete a document

```bash
curl -X DELETE \
  http://127.0.0.1:8001/documents/DOCUMENT_ID \
  -H "Authorization: Bearer $MIRA_TOKEN"
```

Deletion removes:

- Original stored file
- Document database row
- Indexed chunks
- Vector embeddings
- Structured extraction record

### Health checks

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/health/ready
```

---

## 🧪 Testing

### Backend

```bash
cd ~/Projects/MIRA
source .venv/bin/activate

pytest
```

### Frontend unit and component tests

```bash
cd ~/Projects/MIRA/frontend

npm run test
```

Current verified result:

```text
8 test files passed
19 tests passed
```

### Lint and production build

```bash
npm run lint
npm run build
```

### Cypress end-to-end tests

Keep both services running:

```text
Frontend: http://127.0.0.1:5173
Backend:  http://127.0.0.1:8001
```

Run:

```bash
CYPRESS_BASE_URL=http://127.0.0.1:5173 \
npm run test:e2e
```

Current verified result:

```text
2 tests passed
```

The E2E suite verifies:

1. Registration
2. Authenticated upload
3. Grounded document query
4. Source-backed response
5. Permanent document deletion
6. Logout
7. Cross-account document isolation

---

## 📁 Project Structure

```text
MIRA/
├── alembic/
│   ├── env.py
│   └── versions/                    Migration history
├── app/
│   ├── main.py
│   ├── api/routes/
│   │   ├── auth.py                 Registration, login, current user
│   │   ├── documents.py            Owned document management
│   │   ├── extraction.py           Structured extraction API
│   │   ├── health.py               Liveness and readiness
│   │   ├── ingest.py               Authenticated upload and indexing
│   │   └── query.py                Direct, RAG, and web queries
│   ├── core/
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── security.py
│   ├── db/
│   │   ├── models.py
│   │   └── session.py
│   └── services/
│       ├── safety_guard.py
│       ├── auth_service.py
│       ├── document_classifier.py
│       ├── document_service.py
│       ├── cleaner_service.py
│       ├── chunking_service.py
│       ├── embedding_service.py
│       ├── indexing_service.py
│       ├── retrieval_service.py
│       ├── langchain_retriever_service.py
│       ├── langgraph_agent_service.py
│       ├── rag_service.py
│       ├── direct_llm_service.py
│       ├── llm_service.py
│       ├── web_search_service.py
│       ├── medical_prompt_service.py
│       └── extraction_service.py
├── frontend/
│   ├── cypress/
│   │   ├── e2e/
│   │   │   └── mira-workflow.cy.ts
│   │   ├── fixtures/
│   │   └── support/
│   ├── src/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── components/
│   │   ├── layout/
│   │   ├── pages/
│   │   ├── styles/
│   │   ├── test/
│   │   ├── types/
│   │   ├── router.tsx
│   │   └── main.tsx
│   ├── cypress.config.ts
│   ├── vitest.config.ts
│   ├── package.json
│   └── vite.config.ts
├── sample_data/
├── scripts/
├── tests/
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## ✅ Status

### Complete

- [x] FastAPI backend
- [x] PostgreSQL + pgvector + HNSW
- [x] PDF and TXT ingestion
- [x] UUID-based file storage
- [x] SHA-256 duplicate detection
- [x] Medical document classification
- [x] Line-preserving cleaning
- [x] Newline-aware chunking
- [x] Source-cited RAG
- [x] Complete-document summaries
- [x] Multi-document comparison
- [x] Direct Ollama route
- [x] Tavily web search
- [x] Deterministic safety guard
- [x] Deterministic medical disclaimer
- [x] JWT authentication
- [x] Argon2 password hashing
- [x] Per-user document ownership
- [x] Cross-user isolation
- [x] Structured medical extraction
- [x] Persisted extraction records
- [x] Evidence-backed extraction UI
- [x] React + TypeScript frontend
- [x] Protected frontend routes
- [x] Session-expiration handling
- [x] Health and readiness endpoints
- [x] Alembic migrations
- [x] Frontend unit and component tests
- [x] Cypress end-to-end workflows

### Next milestone

- [ ] Provider-neutral LLM interface
- [ ] Dedicated Ollama provider
- [ ] Groq provider
- [ ] Primary and fallback provider configuration
- [ ] Timeout and retry policies
- [ ] Structured-output handling
- [ ] Provider-specific error mapping
- [ ] Latency benchmarking
- [ ] Mocked provider tests

### Future roadmap

- [ ] Deterministic response validation
- [ ] Medical NER
- [ ] Hybrid BM25 + vector retrieval
- [ ] Cross-encoder reranking
- [ ] RAGAS evaluation pipeline
- [ ] Conversation memory with strict ownership
- [ ] Secure HTTP-only cookie authentication
- [ ] Audit logging
- [ ] Encryption at rest
- [ ] Rate limiting
- [ ] Voice interface
- [ ] Production deployment
- [ ] Monitoring and observability dashboards

---

## 🔒 Privacy Notice

MIRA is an authenticated local development system, but it is **not production-ready for real protected health information**.

**Implemented:**

- Password hashing
- JWT authentication
- Per-user ownership
- Authorization checks
- Cross-account isolation
- Permanent deletion

**Still required before real medical use:**

- HTTPS
- Secure HTTP-only cookies
- CSRF protection
- Encryption at rest
- Secret management
- Audit logging
- Rate limiting
- Backup and recovery controls
- Data-retention policies
- Security review
- Compliance assessment
- Production monitoring
- Incident-response procedures

**Use only synthetic medical documents during development.**

---

## Medical Notice

MIRA provides educational explanations of supplied documents. It does not replace a licensed healthcare professional and must not be used for diagnosis, treatment decisions, medication changes, emergency triage, or prognosis.

For urgent symptoms or emergencies, contact local emergency services immediately.

---

## 📝 License

MIT

---

> Built as a safety-first medical document intelligence platform combining authenticated document ownership, LangGraph routing, LangChain-compatible pgvector retrieval, structured extraction, deterministic safety guardrails, source-backed answers, React workflows, and local Ollama inference — with medical disclaimers enforced by application code, never by the language model.