# 🩺 MIRA

### Medical Intelligence and Retrieval Assistant

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?style=flat&logo=react&logoColor=black)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Orchestration-FF6B6B?style=flat)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=flat&logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Primary_LLM-Groq-orange?style=flat)
![Ollama](https://img.shields.io/badge/Local_LLM-Ollama%20%7C%20llama3.2-black?style=flat)
![Cypress](https://img.shields.io/badge/Cypress-E2E_Passing-17202C?style=flat&logo=cypress&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active_Development-yellow?style=flat)

MIRA is a **safety-first medical document intelligence platform** for understanding personal medical records through grounded retrieval, source-linked explanations, structured extraction, bounded conversation memory, and deterministic medical safety controls.

> **MIRA explains what your documents say. It does not make new medical determinations.**

---

## Why MIRA

Medical-document assistants need more than a chatbot interface. They need clear evidence boundaries, strong user isolation, reliable source attribution, and deterministic handling for high-risk medical requests.

MIRA is designed around those constraints:

- answers questions using explicitly selected user-owned documents
- preserves document boundaries during comparison
- links answers back to supporting evidence
- keeps conversation memory separate from document authorization
- blocks diagnosis, prognosis, emergency, and medication-change requests before LLM routing
- appends medical disclaimers in application code rather than relying on the model
- supports hosted and local LLM execution
- evaluates retrieval and generation separately with a synthetic benchmark suite

---

## Core Capabilities

### Document intelligence

- Upload and index PDF or TXT medical records
- SHA-256 duplicate detection
- Medical document classification
- Full-document summarization
- Grounded document Q&A
- Multi-document comparison
- Structured medical fact extraction
- Permanent document deletion

### Retrieval and generation

- Hybrid semantic + BM25 retrieval
- Reciprocal Rank Fusion (RRF)
- Cross-encoder reranking
- PostgreSQL + pgvector with HNSW cosine indexing
- `all-MiniLM-L6-v2` embeddings
- Groq as the primary hosted LLM
- Ollama `llama3.2` as a local fallback
- Tavily for explicitly current/public-information queries

### Conversations

- Persistent user-owned conversations
- Bounded conversation history
- Follow-up question support
- Request-scoped document selection
- No silent reactivation of documents from previous turns
- Prior assistant responses are never treated as medical evidence

### Voice

- Browser-native speech-to-text
- Transcript review before submission
- Browser-native text-to-speech
- Listen / Pause / Resume / Stop / Replay
- Source markers and Markdown removed from spoken text
- Playback cancelled when conversations change

---

## Evidence-First UI

The frontend uses a calm navy/blue workspace designed around evidence rather than chat alone.

The **Ask MIRA** experience uses a split layout:

```text
┌──────────────────────────────┬──────────────────────────────┐
│ Evidence                     │ Ask MIRA                     │
│                              │                              │
│ Supporting source passage    │ User question                │
│ highlighted in context       │                              │
│                              │ Grounded answer [1]          │
│ Source / document metadata   │                              │
│                              │ Composer + voice controls    │
└──────────────────────────────┴──────────────────────────────┘
```

Citation badges in answers connect directly to the corresponding evidence shown in the left pane. This reduces source-card clutter while keeping the grounding visible.

Other UI workflows include:

- authentication and protected routes
- document upload/review/deletion
- dashboard overview
- extraction review
- medical intelligence summaries
- conversation creation, switching, and deletion
- responsive layouts
- accessible form controls and navigation

---

## Safety Architecture

High-risk medical requests are handled **before** LangGraph routing, retrieval, or any LLM call.

```text
User Query
    ↓
Deterministic Safety Guard
    ├── Emergency request          → Immediate emergency guidance
    ├── Self-harm indicator        → Crisis-oriented response
    ├── Diagnosis request          → Redirect to healthcare professional
    ├── Prognosis request          → Decline outcome prediction
    └── Medication-change request  → Refuse treatment-change guidance
    ↓
Allowed Query
    ↓
Conversation-aware LangGraph routing
    ├── Selected documents         → Grounded RAG
    ├── Multi-document comparison  → Complete selected-document retrieval
    ├── Explicit latest/current    → Tavily web search
    └── General education          → Direct LLM
    ↓
Response validation / repair
    ↓
Deterministic medical disclaimer
    ↓
Conversation persistence
    ↓
Source-linked response
```

### Evidence boundary

Conversation memory improves continuity, but it never expands document authorization.

```text
Conversation memory ≠ document evidence
```

- current document selection controls the evidence scope
- historical document IDs are not silently restored
- prior user questions may help interpret follow-ups
- prior assistant messages are not treated as source evidence

---

## Retrieval Pipeline

```text
Authenticated PDF / TXT upload
        ↓
Filename, extension, and size validation
        ↓
SHA-256 duplicate detection
        ↓
Text extraction and cleaning
        ↓
Overlapping chunk generation
        ↓
Medical document classification
        ↓
SentenceTransformer embeddings
        ↓
PostgreSQL + pgvector
        ↓
Hybrid semantic + BM25 retrieval
        ↓
Reciprocal Rank Fusion
        ↓
Cross-encoder reranking
        ↓
Context construction
        ↓
Grounded generation + validation
```

For summaries and selected multi-document workflows, MIRA can use complete-document retrieval to avoid losing important sections to similarity search alone.

---

## RAG Evaluation

MIRA includes a deterministic evaluation harness built on **12 synthetic cases across four synthetic medical documents**.

The benchmark measures retrieval separately from final production-RAG behavior.

| Metric | Result |
|---|---:|
| Retrieval Hit@3 | 1.000 |
| Retrieval Recall@3 | 1.000 |
| Retrieval MRR | 0.944 |
| Wrong-document rate | 0.037 |
| Context document recall | 1.000 |
| Required-fact survival | 1.000 |
| Evidence retention | 1.000 |
| Final required-fact recall | 0.958 |
| Abstention accuracy | 1.000 |
| Grounded-answer pass rate | 1.000 |
| Unsupported medical-value rate | 0.000 |
| Invalid citation rate | 0.000 |
| Misattributed medical-value rate | 0.000 |
| End-to-end case success | 0.833 |

The current end-to-end benchmark passes **10 of 12 cases**. The two known failures are intentionally retained rather than hidden:

- `qa_medication_lisinopril` — answer omitted the documented frequency `once daily`
- `distractor_glucose` — deterministic fallback included the distractor value `96 mg/dL`

See:

- [`evaluation/README.md`](evaluation/README.md)
- [`evaluation/reports/RAG_EVALUATION_REPORT.md`](evaluation/reports/RAG_EVALUATION_REPORT.md)

### Benchmark scope

This is a small synthetic engineering benchmark, not a clinical validation study. Many cases operate over explicitly selected documents, so the results should not be presented as broad corpus-wide retrieval performance.

---

## Authentication, Privacy, and Isolation

Implemented controls include:

- email/password authentication
- Argon2 password hashing
- JWT-based authenticated sessions
- HttpOnly authentication cookies in the browser workflow
- protected frontend and backend routes
- per-user document ownership
- per-user conversation ownership
- per-user duplicate detection
- authorization checks for query, extraction, conversation access, and deletion
- React Query cache clearing between users
- request rate limiting
- permanent deletion workflows
- deterministic medical safety guards

> MIRA is a development system and is **not production-ready for real protected health information**.

Use synthetic medical documents during development.

---

## Observability

MIRA includes Prometheus metrics and Grafana dashboards for service and RAG behavior.

Observed areas include:

- query execution
- routing
- retrieval
- LLM/provider activity
- safety decisions
- service health

Metrics are designed to remain low-cardinality and avoid medical text, filenames, document IDs, conversation IDs, prompts, or other sensitive values in labels.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Routing | React Router |
| Server state | TanStack Query |
| Styling | CSS |
| Backend | FastAPI |
| Authentication | JWT, HttpOnly cookies, Argon2 |
| Agent orchestration | LangGraph |
| Retrieval | Semantic search + BM25 + RRF + cross-encoder reranking |
| Embeddings | SentenceTransformers `all-MiniLM-L6-v2` |
| Vector database | PostgreSQL + pgvector |
| Vector index | HNSW cosine |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Hosted LLM | Groq |
| Local LLM | Ollama `llama3.2` |
| Web search | Tavily |
| PDF parsing | pypdf |
| Observability | Prometheus, Grafana |
| Backend tests | Pytest |
| Frontend tests | Vitest, Testing Library |
| E2E tests | Cypress |
| Local development | WSL2, Linux, Docker |

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/Bteja272/MIRA.git
cd MIRA
```

### 2. Backend environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Use `.env.example` as the development configuration reference. Do not commit `.env`.

### 3. Start PostgreSQL + pgvector

```bash
docker compose up -d
docker compose ps
```

### 4. Apply migrations

```bash
python -m alembic -c alembic.ini upgrade head
```

### 5. Optional local Ollama

```bash
ollama pull llama3.2
ollama serve
```

### 6. Start the backend

```bash
python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8001 \
  --reload
```

API: `http://127.0.0.1:8001`  
OpenAPI docs: `http://127.0.0.1:8001/docs`

### 7. Start the frontend

```bash
cd frontend
npm ci
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8001
```

Then:

```bash
npm run dev
```

Frontend: `http://127.0.0.1:5173`

---

## Testing

### Backend

```bash
cd ~/Projects/MIRA
source .venv/bin/activate
pytest
```

### Deterministic RAG regression

```bash
./scripts/run_rag_eval_regression.sh
```

The current RAG regression suite contains **42 passing tests**.

### Frontend unit/component tests

```bash
cd ~/Projects/MIRA/frontend
npm run test -- --run
```

Current verified frontend suite:

```text
14 test files
60 tests passed
```

### Production build

```bash
npm run build
```

### Cypress E2E

For local E2E runs that create multiple synthetic accounts, use development-only rate-limit overrides:

```bash
RATE_LIMIT_REGISTER_REQUESTS=100 \
RATE_LIMIT_REGISTER_WINDOW_SECONDS=60 \
RATE_LIMIT_LOGIN_REQUESTS=100 \
RATE_LIMIT_LOGIN_WINDOW_SECONDS=60 \
python -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8001 \
  --reload
```

Then:

```bash
cd ~/Projects/MIRA/frontend
npx cypress run
```

The current Cypress suite passes across authentication, session security, document workflows, cross-account isolation, conversations, medical intelligence, speech-to-text, text-to-speech, and combined voice interaction.

Production rate-limit defaults should not be weakened for test convenience.

---

## Project Structure

```text
MIRA/
├── app/
│   ├── api/routes/
│   ├── core/
│   ├── db/
│   └── services/
├── frontend/
│   ├── cypress/e2e/
│   └── src/
│       ├── api/
│       ├── auth/
│       ├── components/
│       ├── hooks/
│       ├── layout/
│       ├── pages/
│       ├── styles/
│       ├── types/
│       └── voice/
├── evaluation/
│   ├── datasets/
│   ├── reports/
│   ├── end_to_end_evaluator.py
│   ├── end_to_end_runner.py
│   ├── final_rag_runner.py
│   ├── generation_evaluator.py
│   ├── live_retrieval_runner.py
│   └── rag_evaluation_report.py
├── scripts/
│   └── run_rag_eval_regression.sh
├── tests/
├── alembic/
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## Current Status

### Complete

- FastAPI backend
- PostgreSQL + pgvector
- PDF/TXT ingestion
- source-grounded RAG
- hybrid retrieval and reranking
- complete-document summaries
- multi-document comparison
- deterministic medical safety guard
- authentication and per-user isolation
- persistent bounded conversations
- structured medical extraction
- React + TypeScript frontend
- redesigned evidence-first UI
- speech-to-text and text-to-speech
- Prometheus + Grafana observability
- deterministic RAG evaluation
- frontend unit/component regression coverage
- Cypress end-to-end coverage

### Remaining roadmap

- **11C — Performance benchmarking**
- **11D — Production hardening**
- **11E — Deployment**
- **11F — Portfolio / demo polish**

Production-readiness work still includes HTTPS, secrets management, encryption-at-rest strategy, backup/restore validation, security review, deployment smoke tests, and production infrastructure.

---

## Medical and Privacy Notice

MIRA provides educational explanations of supplied documents. It does not replace a licensed healthcare professional and must not be used for diagnosis, treatment decisions, medication changes, emergency triage, or prognosis.

The project has not established HIPAA compliance, clinical efficacy, or suitability for autonomous medical decision-making.

For urgent symptoms or emergencies, contact local emergency services immediately.

---

## License

MIT
