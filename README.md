# 🩺 MIRA

### Medical Intelligence and Retrieval Assistant

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?style=flat&logo=react&logoColor=black)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Orchestration-FF6B6B?style=flat)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=flat&logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Primary_LLM-Groq-orange?style=flat)
![Ollama](https://img.shields.io/badge/Local_LLM-Ollama_%7C_llama3.2-black?style=flat)
![Tavily](https://img.shields.io/badge/Search-Tavily-blue?style=flat)
![Vitest](https://img.shields.io/badge/Vitest-Passing-6E9F18?style=flat&logo=vitest&logoColor=white)
![Cypress](https://img.shields.io/badge/Cypress-E2E_Passing-17202C?style=flat&logo=cypress&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active_Development-yellow?style=flat)

> You upload a medical document. You ask: **"What medications and follow-up instructions are documented here?"** MIRA retrieves evidence from your selected record, explains it in plain English, cites the source, persists the conversation, and appends a deterministic medical disclaimer — without diagnosing you or recommending treatment changes.

---

## What MIRA Is

MIRA is a **safety-first medical document intelligence platform** for understanding personal medical records.

It combines authenticated document ownership, retrieval-augmented generation, structured medical extraction, bounded conversation memory, deterministic safety checks, current-information web search, and a React + TypeScript interface with browser-native voice input and text-to-speech.

> **MIRA explains what your documents say. It does not make new medical determinations.**

### What MIRA does

- Register and authenticate users
- Keep each user's documents and conversations isolated
- Upload and index PDF or TXT medical records
- Summarize medical documents
- Answer grounded questions using explicitly selected documents
- Compare multiple documents while preserving source boundaries
- Explain medical terminology
- Search current public information through Tavily
- Extract structured medical facts with supporting evidence
- Persist bounded conversation history for follow-up questions
- Keep document selection request-scoped
- Accept speech-to-text input for question drafting
- Read assistant responses aloud through browser text-to-speech
- Permanently delete documents and associated indexed data

### What MIRA never does

- Diagnose conditions based on symptoms
- Recommend changing, stopping, starting, or adjusting medication
- Predict prognosis
- Treat generated text as a substitute for a licensed professional
- Allow cross-user access to documents or conversations
- Treat prior assistant responses as medical evidence
- Skip deterministic medical safety behavior

---

## Current User Experience

### Frontend workflows

- Registration and login
- Protected routes
- Document upload, duplicate detection, review, and permanent deletion
- Multi-document selection
- Conversation creation, history, switching, and deletion
- Bounded follow-up memory
- Grounded Q&A with source cards
- Current-information answers with web sources
- Structured medical extraction and evidence review
- Browser-native speech-to-text
- Browser-native text-to-speech
- Listen / Pause / Resume / Stop / Replay
- Session-expiration handling
- Offline/network feedback
- Accessible forms and navigation

### Voice behavior

**Speech-to-text**

- Uses the browser Web Speech API when available
- Inserts recognized text into the composer
- Does **not** auto-submit medical questions
- Leaves the transcript visible for review

**Text-to-speech**

- Reads only assistant answer text
- Does not read source cards or route metadata
- Removes source markers such as `[Source 1]`
- Removes Markdown emphasis symbols before playback
- Supports Listen, Pause, Resume, Stop, and Replay
- Cancels playback when starting or switching conversations
- Cancels previous speech before a new utterance begins

### Main frontend routes

| Route | Purpose |
|---|---|
| `/register` | Create an account |
| `/login` | Authenticate |
| `/` | Dashboard |
| `/documents` | Upload, review, and delete documents |
| `/ask` | Ask direct, grounded, current-information, or follow-up questions |
| `/extractions` | Generate and review structured medical facts |

---

## Safety Architecture

Medical-risk queries are blocked **before** LangGraph routing, retrieval, or any LLM call.

```text
User Query
     ↓
Deterministic Safety Guard
     │
     ├── Emergency request          → Immediate emergency guidance
     ├── Self-harm indicator       → Crisis-oriented response
     ├── Diagnosis request         → Redirect to a healthcare provider
     ├── Prognosis request         → Decline outcome prediction
     └── Medication-change request → Refuse medication-change guidance
     ↓
Allowed Query
     ↓
Conversation-aware LangGraph routing
     │
     ├── Selected documents        → pgvector RAG
     ├── Multi-document comparison → Complete selected-document retrieval
     ├── Explicit latest/current   → Tavily web search
     └── General education         → Direct LLM generation
     ↓
Application validation
     ↓
Deterministic medical disclaimer
     ↓
Conversation persistence
     ↓
Source-cited response
     ↓
Optional browser text-to-speech
```

The disclaimer is appended by application code rather than generated conditionally by the model.

### Evidence boundary

Conversation memory improves continuity, but it does not replace evidence.

- Current document selection controls the document scope of the request
- Historical document IDs are not silently reactivated
- Prior user questions can help interpret a follow-up
- Prior assistant answers are not treated as medical source evidence

---

## Conversation Memory

MIRA supports persistent, user-owned conversations.

- Conversations and messages are stored in PostgreSQL
- Access is scoped to the authenticated owner
- Context is bounded before reuse
- Follow-up questions can use prior conversational context
- Document selection remains request-scoped
- Starting a new conversation resets the active thread
- Switching conversations clears current document selection
- Deleting a conversation removes its stored messages
- Cross-account conversation access is blocked

```text
Conversation memory
        ≠
Document authorization / document selection
```

This prevents a prior document from silently grounding a later medical answer.

---

## Authentication, Security, and Data Isolation

### Implemented controls

- Email/password registration
- Argon2 password hashing
- JWT authentication
- Protected backend and frontend routes
- Per-user document ownership
- Per-user conversation ownership
- Per-user duplicate detection
- Authorization checks for query, extraction, conversation access, and deletion
- Cross-user isolation
- React Query cache clearing between users
- Invalid/expired-session handling
- Request rate limiting
- Permanent deletion workflows
- Deterministic medical safety guards

MIRA remains a development system and is **not production-ready for real protected health information**.

---

## What Makes This Different From Generic RAG

| Problem | MIRA approach |
|---|---|
| Similarity search omits sections | Complete-document retrieval for summaries |
| Multi-document facts become mixed | Document boundaries preserved in prompts |
| Model independently labels lab values | Only documented flags are reproduced |
| LLM could skip disclaimer | Disclaimer appended deterministically |
| Emergency requests reach the LLM | Pre-routing safety guard blocks them first |
| Duplicate files pollute retrieval | SHA-256 duplicate detection |
| Cross-user data exposure | Ownership checks on documents and conversations |
| Old documents affect follow-ups | Document selection remains request-scoped |
| Assistant text becomes evidence | Generated assistant text is not medical evidence |
| Citation markup sounds wrong in TTS | Spoken text is sanitized before synthesis |
| Schema drift | Alembic migrations |

---

## Routing Table

| Request | Route | Reason |
|---|---|---|
| "Summarize this report" | Full-document RAG | Avoids missing sections |
| "What medications are documented here?" | Selected-document RAG | Must remain grounded |
| "Compare these reports" | Multi-document RAG | Preserves source boundaries |
| Follow-up about selected medical evidence | Conversation-aware RAG | Uses bounded intent plus current selection |
| "What does HbA1c mean?" | Direct LLM | General education |
| "What are the latest public guidelines?" | Tavily web search | Requires current information |
| "Should I stop this medication?" | Safety guard | Medication-change guidance blocked |
| "I have chest pain right now" | Safety guard | Emergency handling occurs first |

---

## Structured Medical Extraction

MIRA can turn an owned document into persisted structured medical facts with evidence.

Current categories include:

- Patient information
- Diagnoses
- Medications
- Allergies
- Procedures
- Follow-up instructions
- Additional schema-supported facts

Each fact may include normalized value, supporting evidence, source filename, document ID, and page/chunk position.

---

## Document Ingestion Pipeline

```text
Authenticated PDF / TXT upload
     ↓
Filename and extension validation
     ↓
25 MB upload limit
     ↓
UUID-based stored filename
     ↓
SHA-256 duplicate detection
     ↓
Text extraction
     ↓
Line-preserving cleaning
     ↓
Newline-aware overlapping chunking
     ↓
Medical document classification
     ↓
SentenceTransformers all-MiniLM-L6-v2 embeddings
     ↓
PostgreSQL + pgvector · HNSW cosine index
```

Supported document types:

`lab_report` · `discharge_summary` · `prescription` · `imaging_report` · `pathology_report` · `visit_note` · `vaccination_record` · `insurance_document` · `unknown`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Routing | React Router |
| Server state | TanStack Query |
| Styling | Plain CSS |
| Voice input | Browser Web Speech API |
| Text-to-speech | Browser Speech Synthesis API |
| Backend | FastAPI |
| Authentication | JWT, Argon2 |
| Agent orchestration | LangGraph |
| Retrieval | LangChain-compatible retriever |
| Embeddings | SentenceTransformers `all-MiniLM-L6-v2` |
| Vector database | PostgreSQL + pgvector |
| Vector index | HNSW cosine |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Primary hosted LLM | Groq |
| Local LLM | Ollama · `llama3.2` |
| Web search | Tavily |
| Document parsing | pypdf |
| Database container | Docker Compose |
| Frontend testing | Vitest, Testing Library |
| E2E testing | Cypress |
| Backend testing | Pytest |
| Development | WSL2, Linux, Docker |

---

## 🏗️ Key Technical Decisions

**Why deterministic safety before LangGraph?**  
Medical-risk handling should not depend on an LLM recognizing a dangerous request correctly.

**Why complete-document retrieval for summaries?**  
A semantic search query may not match every clinically relevant section.

**Why preserve document boundaries?**  
It reduces the risk of assigning a medication, date, lab value, or diagnosis to the wrong record.

**Why keep document selection request-scoped?**  
Conversation continuity should not silently reactivate evidence from an earlier turn.

**Why not treat assistant messages as evidence?**  
Generated text may contain interpretation. Original documents remain the grounding source.

**Why does speech-to-text not auto-submit?**  
Medical numbers, units, medication names, and terminology can be mistranscribed, so the transcript remains editable before submission.

**Why sanitize TTS text?**  
Citation markers and Markdown symbols are useful on screen but may be read literally by browser speech engines.

---

## 🚀 Quick Start

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

Use `.env.example` as the source of truth for development configuration. Do not commit `.env`.

Typical local values include:

```env
DATABASE_URL=postgresql+psycopg://...
TAVILY_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 3. PostgreSQL + pgvector

```bash
docker compose up -d
docker compose ps
```

### 4. Migrations

```bash
python -m alembic -c alembic.ini upgrade head
```

### 5. Local Ollama

```bash
ollama pull llama3.2
ollama serve
```

### 6. Backend

```bash
python -m uvicorn app.main:app   --host 127.0.0.1   --port 8001   --reload
```

API: `http://127.0.0.1:8001`  
Docs: `http://127.0.0.1:8001/docs`

### 7. Frontend

```bash
cd frontend
npm ci
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8001
```

Run:

```bash
npm run dev
```

Frontend: `http://127.0.0.1:5173`

---

## 🔌 API Examples

### Register

```bash
curl -X POST http://127.0.0.1:8001/auth/register   -H "Content-Type: application/json"   -d '{
    "email": "synthetic.user@example.com",
    "password": "SyntheticPassword!2026"
  }'
```

### Login

```bash
curl -X POST http://127.0.0.1:8001/auth/login   -H "Content-Type: application/x-www-form-urlencoded"   -d "username=synthetic.user@example.com&password=SyntheticPassword!2026"
```

### Query selected documents

```bash
curl -X POST http://127.0.0.1:8001/query   -H "Authorization: Bearer $MIRA_TOKEN"   -H "Content-Type: application/json"   -d '{
    "query": "Summarize this document.",
    "document_ids": ["DOCUMENT_ID"]
  }'
```

### Continue a conversation

```bash
curl -X POST http://127.0.0.1:8001/query   -H "Authorization: Bearer $MIRA_TOKEN"   -H "Content-Type: application/json"   -d '{
    "query": "What follow-up was documented?",
    "document_ids": ["DOCUMENT_ID"],
    "conversation_id": "CONVERSATION_ID"
  }'
```

### Health

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

### Frontend unit/component suite

```bash
cd ~/Projects/MIRA/frontend
npm run test -- --run
```

### Production build

```bash
npm run build
```

### Cypress

For development E2E runs that create many synthetic accounts, start the backend with local-only rate-limit overrides:

```bash
RATE_LIMIT_REGISTER_REQUESTS=100 RATE_LIMIT_REGISTER_WINDOW_SECONDS=60 RATE_LIMIT_LOGIN_REQUESTS=100 RATE_LIMIT_LOGIN_WINDOW_SECONDS=60 uvicorn app.main:app --reload --port 8001
```

Then:

```bash
cd ~/Projects/MIRA/frontend
npx cypress run
```

Current E2E coverage includes authentication, document workflows, cross-account isolation, conversations, speech-to-text, text-to-speech, spoken-text sanitization, and conversation-transition playback cancellation.

Production rate-limit defaults should not be weakened for test convenience.

---

## 📁 Project Structure

```text
MIRA/
├── alembic/
├── app/
│   ├── api/routes/
│   │   ├── auth.py
│   │   ├── conversations.py
│   │   ├── documents.py
│   │   ├── extraction.py
│   │   ├── health.py
│   │   ├── ingest.py
│   │   └── query.py
│   ├── core/
│   ├── db/
│   └── services/
├── frontend/
│   ├── cypress/e2e/
│   │   ├── mira-workflow.cy.ts
│   │   ├── mira-conversations.cy.ts
│   │   ├── mira-voice.cy.ts
│   │   └── mira-tts.cy.ts
│   └── src/
│       ├── api/
│       ├── auth/
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       ├── styles/
│       ├── types/
│       └── voice/
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
- [x] PDF/TXT ingestion
- [x] Duplicate detection
- [x] Medical document classification
- [x] Source-cited RAG
- [x] Complete-document summaries
- [x] Multi-document comparison
- [x] Tavily web search
- [x] Deterministic safety guard
- [x] Deterministic medical disclaimer
- [x] JWT authentication + Argon2
- [x] Per-user document isolation
- [x] Structured medical extraction
- [x] React + TypeScript frontend
- [x] Alembic migrations
- [x] Request rate limiting
- [x] Persistent conversations
- [x] Per-user conversation ownership
- [x] Bounded conversation memory
- [x] Request-scoped document selection
- [x] Browser speech-to-text
- [x] Browser text-to-speech
- [x] Listen / Pause / Resume / Stop / Replay
- [x] TTS source/Markdown sanitization
- [x] Playback cancellation on conversation transitions
- [x] Frontend unit/component coverage
- [x] Cypress E2E coverage

### Current milestone

- [ ] Coordinate STT and TTS across the same conversation flow
- [ ] Harden voice-state transitions
- [ ] Add combined voice integration tests
- [ ] Run final voice regression

### Production milestone

- [ ] Production environment separation
- [ ] HTTPS
- [ ] Secure HTTP-only cookie authentication
- [ ] CSRF protection
- [ ] Managed PostgreSQL + pgvector
- [ ] Production file-storage strategy
- [ ] Secret management
- [ ] Encryption-at-rest strategy
- [ ] Audit logging
- [ ] Backup/restore validation
- [ ] Monitoring and observability
- [ ] Deployment smoke tests
- [ ] Production UI refinement

### Future retrieval/evaluation roadmap

- [ ] Hybrid BM25 + vector retrieval
- [ ] Cross-encoder reranking
- [ ] RAG evaluation pipeline
- [ ] Expanded retrieval benchmarking
- [ ] Additional medical NER where useful

---

## 🔒 Privacy Notice

MIRA is an authenticated development system, but it is **not production-ready for real protected health information**.

### Implemented

- Password hashing
- JWT authentication
- Per-user document ownership
- Per-user conversation ownership
- Authorization checks
- Cross-account isolation
- Permanent deletion
- Request rate limiting
- Deterministic safety controls
- Synthetic-data development workflow

### Still required before real medical use

- HTTPS
- Secure HTTP-only cookies
- CSRF protection
- Encryption at rest
- Secret management
- Audit logging
- Backup/recovery controls
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

> Built as a safety-first medical document intelligence platform combining authenticated document ownership, bounded conversation memory, LangGraph routing, pgvector retrieval, structured extraction, deterministic safety guardrails, source-backed answers, React workflows, browser-native voice interaction, hosted/local LLM support, and medical disclaimers enforced by application code.
