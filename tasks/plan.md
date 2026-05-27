# Vocra — Implementation Plan

**Date:** 2026-05-25  
**Approach:** Vertical slices — each task delivers one complete working path, not a horizontal layer.

---

## Current State Audit

### What exists (Phase 1 Backend — COMPLETE)

| Component | Status | Location |
|-----------|--------|----------|
| FastAPI app + CORS + lifespan | ✅ Done | `backend/app/main.py` |
| SQLite + SQLAlchemy 2.0 session | ✅ Done | `backend/app/database/` |
| `Application` model (soft delete) | ✅ Done | `backend/app/models/application.py` |
| Applications CRUD API (5 endpoints) | ✅ Done | `backend/app/api/applications.py` |
| Applications service layer | ✅ Done | `backend/app/services/applications.py` |
| Pydantic v2 schemas | ✅ Done | `backend/app/schemas/application.py` |
| `GET /api/health` | ✅ Done | `backend/app/main.py` |
| Storage directories (resumes/exports/backups) | ✅ Done | `backend/storage/` |
| Conda env + requirements.txt | ✅ Done | `backend/environment.yml` |
| Dev script | ✅ Done | `scripts/dev-backend.sh` |

### What does NOT exist yet

- **Frontend**: directory is empty — no React, no Vite, no UI at all
- **Resume system**: no model, no upload API, no PDF/DOCX parsing
- **Skill extraction**: no service, no extracted_skills table
- **ATS matching**: no matching engine, no match_results table
- **Ollama integration**: no client, no prompt templates, no ai_cache table
- **Interview prep**: no generation service, no interview_prep table
- **Dashboard analytics**: no aggregate queries, no dashboard API
- **Alembic migrations**: DB created via `init_db()` — no migration chain
- **Missing packages**: pymupdf, python-docx, spaCy, rapidfuzz, scikit-learn not in requirements
- **FTS5 search**: currently uses ILIKE — not yet upgraded to SQLite FTS5

---

## Dependency Graph

```
[P1] Backend Foundation ✅
        │
        ├──► [P2] Frontend Foundation + Applications UI
        │           │
        │           └──► All frontend slices depend on this
        │
        ├──► [P3] Resume System (backend)
        │           │
        │           ├──► [P4] Matching Engine (needs resume + JD text)
        │           │           │
        │           │           └──► [P5-B] Resume Improvement via LLM
        │           │
        │           └──► Frontend Resume UI (needs P2 + P3 backend)
        │
        ├──► [P5-A] Ollama Client + Cache (independent of resume system)
        │           │
        │           └──► [P5-C] Interview Prep (needs P3 + P5-A)
        │
        └──► [P6] Dashboard Analytics (needs P1 + applications data)
```

Critical path: **P1 → P3 → P4 → P5 → P6** (backend)  
Parallel track: **P2 (frontend)** can start immediately alongside P3.

---

## Phases

---

### Phase 2 — Applications Frontend (Vertical Slice 1)

**Goal:** First working UI — users can manage applications in the browser.  
**Estimate:** 3–4 days  
**Depends on:** Phase 1 (complete)

#### Task 2.1 — Initialize React + Vite frontend

**What to build:**  
Scaffold `frontend/` with Vite + React + JavaScript + Tailwind CSS + shadcn/ui.

**Steps:**
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install tailwindcss @tailwindcss/vite
npx shadcn@latest init
npm install react-router-dom @tanstack/react-query axios zustand react-hook-form @hookform/resolvers zod recharts
```

**Acceptance criteria:**
- `npm run dev` starts at `localhost:5173` with no errors
- Tailwind styles apply (test with a colored div)
- shadcn/ui Button component renders correctly
- JavaScript strict mode enabled in `tsconfig.json`

**Verification:** Open browser at localhost:5173, see Vocra heading with a shadcn Button.

---

#### Task 2.2 — App shell: layout + routing

**What to build:**  
Root layout with sidebar nav + main content area. Routes for all 5 sections (stubbed pages).

**File targets:**
- `frontend/src/layouts/AppLayout.tsx` — sidebar + outlet
- `frontend/src/pages/ApplicationsPage.tsx` (stub)
- `frontend/src/pages/ResumesPage.tsx` (stub)
- `frontend/src/pages/AnalysisPage.tsx` (stub)
- `frontend/src/pages/InterviewPage.tsx` (stub)
- `frontend/src/pages/DashboardPage.tsx` (stub)

**Acceptance criteria:**
- Sidebar shows icons + labels: Applications, Resumes, Analysis, Interview Prep, Dashboard
- Clicking nav items routes correctly (no full reload)
- Active route highlighted in sidebar
- Layout fills viewport, main area scrolls independently

---

#### Task 2.3 — API client + TanStack Query setup

**What to build:**  
Typed API client wrapping `fetch`/`axios`, TanStack Query provider, typed hooks for applications.

**File targets:**
- `frontend/src/services/api.ts` — base client with `BASE_URL = http://localhost:8000/api`
- `frontend/src/services/applications.ts` — typed request functions
- `frontend/src/hooks/useApplications.ts` — TanStack Query hooks
- `frontend/src/types/application.ts` — JavaScript types mirroring backend schemas

**Acceptance criteria:**
- `useApplications()` hook fetches from backend and returns typed data
- Loading and error states handled
- Query invalidation works after mutations

---

#### Task 2.4 — Applications list page

**What to build:**  
Table view with search input, status filter dropdown, pagination.

**Acceptance criteria:**
- Table shows: Company, Title, Status (badge), Date Applied, Salary, Actions
- Search input filters in real-time (debounced, 300ms)
- Status dropdown filters by ApplicationStatus enum
- Empty state shows "No applications yet" with CTA
- Loading skeleton shown while fetching
- Row click navigates to detail page

---

#### Task 2.5 — Create/Edit application form

**What to build:**  
Modal (shadcn Dialog) with React Hook Form + Zod validation for all application fields.

**Acceptance criteria:**
- "Add Application" button opens modal
- All fields from `ApplicationCreate` schema present
- Zod validation: company_name and job_title required, salary_max ≥ salary_min
- Submit calls POST /api/applications, closes modal, refreshes list
- Edit mode pre-populates fields, calls PUT /api/applications/{id}
- Validation errors shown inline under each field

---

#### Task 2.6 — Application detail page + inline status update + delete

**What to build:**  
Full detail view showing all fields, inline status change, delete with confirmation.

**Acceptance criteria:**
- All fields displayed (including job description in a scrollable textarea)
- Status can be changed via dropdown, auto-saves on change (PUT /api/applications/{id})
- "Delete" button shows confirmation dialog before soft-deleting
- Back navigation to list preserves search/filter state (via URL params)
- Follow-up date shows warning badge if in the past

---

**CHECKPOINT 2:** Applications CRUD works end-to-end in browser. User can add, view, edit, filter, delete applications. Backend at localhost:8000, frontend at localhost:5173.

---

### Phase 3 — Resume System (Vertical Slice 2)

**Goal:** Upload PDF/DOCX resumes, extract text, link to applications.  
**Estimate:** 3–4 days  
**Depends on:** Phase 1 (backend), Phase 2 (frontend shell)

#### Task 3.1 — Resume model + DB table

**What to build:**  
`Resume` SQLAlchemy model. Update `init_db` to create the table.

**File targets:**
- `backend/app/models/resume.py`
- Update `backend/app/database/__init__.py` to import Resume model

**Schema:**
```sql
id, name, original_filename, file_path, tags (JSON), version, parsed_text, created_at
```

**Acceptance criteria:**
- `Resume` model importable from `app.models.resume`
- `init_db()` creates `resumes` table in SQLite
- `resume_id` FK in `applications` table references `resumes.id` (add FK constraint)

---

#### Task 3.2 — Add parsing dependencies

**What to build:**  
Add pymupdf, python-docx to requirements and environment.yml.

```
pymupdf>=1.24.0
python-docx>=1.1.0
rapidfuzz>=3.9.0
```

**Acceptance criteria:**
- `conda env update -f environment.yml --prune` succeeds
- `import fitz`, `import docx`, `import rapidfuzz` all work in the conda env

---

#### Task 3.3 — Resume text extraction service

**What to build:**  
`backend/app/parsers/resume_parser.py` — extracts clean text from PDF and DOCX.

**Interface:**
```python
def extract_text(file_path: Path, mime_type: str) -> str: ...
```

**Rules:**
- PDF: use `fitz.open()` (pymupdf), iterate pages, join text blocks
- DOCX: use `python-docx`, extract paragraph text
- Strip excessive whitespace, normalize unicode
- Return empty string (not raise) on malformed files

**Acceptance criteria:**
- Given a valid PDF resume, returns non-empty string containing readable text
- Given a valid DOCX resume, returns non-empty string
- Given a corrupted file, returns empty string without raising
- No LLM calls in this service

---

#### Task 3.4 — Resume upload + list + detail API

**What to build:**  
`backend/app/api/resumes.py` + `backend/app/services/resumes.py` + schemas.

**Endpoints:**
```
POST  /api/resumes/upload   — multipart/form-data: file + optional name/tags/version
GET   /api/resumes           — list all resumes (id, name, tags, version, created_at)
GET   /api/resumes/{id}      — full resume record including parsed_text
DELETE /api/resumes/{id}     — soft delete (add is_deleted field)
```

**Acceptance criteria:**
- Upload accepts only .pdf and .docx (reject others with 422)
- File size limit: 10MB (reject with 413)
- Filename sanitized before saving to storage/resumes/
- parsed_text populated at upload time via Task 3.3 service
- GET /api/resumes returns list sorted by created_at desc
- GET /api/resumes/{id} returns full record

---

#### Task 3.5 — Frontend Resume management page

**What to build:**  
Resume upload dropzone + resume list cards.

**Acceptance criteria:**
- File dropzone accepts PDF/DOCX, shows file name + size before upload
- Upload button POSTs to /api/resumes/upload with progress indicator
- After upload, resume appears in list immediately (query invalidation)
- Each resume card shows: name, version tag, upload date, "View" and "Delete" actions
- Delete shows confirmation dialog

---

#### Task 3.6 — Link resume to application

**What to build:**  
Add resume selector to the Create/Edit Application form (Task 2.5).

**Acceptance criteria:**
- Dropdown in application form lists all uploaded resumes by name
- Selected resume_id saved with application
- Application detail page shows linked resume name (with link to resume detail)
- Unlink option (set resume_id to null)

---

**CHECKPOINT 3:** User can upload a PDF resume → see extracted text → link it to a job application. Full vertical slice working.

---

### Phase 4 — ATS Matching Engine (Vertical Slice 3)

**Goal:** Deterministic resume vs JD matching with ATS score.  
**Estimate:** 4–5 days  
**Depends on:** Phase 3 (resume text available)

#### Task 4.1 — Add NLP dependencies + skill dictionary

**What to build:**  
Add spaCy + scikit-learn to requirements. Create tech skill keyword dictionary.

**Dependencies:**
```
spacy>=3.7.0
scikit-learn>=1.5.0
```
Post-install: `python -m spacy download en_core_web_sm`

**File targets:**
- `backend/app/parsers/skill_dictionary.py` — hardcoded dict of ~200 tech skills/frameworks grouped by category

**Acceptance criteria:**
- spaCy pipeline loads without error
- Skill dictionary covers: languages (Python, Java, JS, TS, Go, Rust…), frameworks (React, FastAPI, Django, Spring…), tools (Docker, Git, AWS, GCP…), concepts (REST API, microservices, CI/CD…)

---

#### Task 4.2 — Extracted skills + match results models

**What to build:**  
Two new SQLAlchemy models.

**`extracted_skills` table:**
```sql
id, source_type (resume|jd), source_id (resume_id or application_id),
skill_name, skill_type, importance_score, created_at
```

**`match_results` table:**
```sql
id, application_id, resume_id, match_score (float),
matching_keywords (JSON), missing_keywords (JSON),
recommendations (JSON), created_at
```

**Acceptance criteria:**
- Both tables created by `init_db()`
- Models importable, relationships navigable

---

#### Task 4.3 — Keyword extraction service

**What to build:**  
`backend/app/services/skill_extractor.py` — deterministic skill extraction from any text.

**Pipeline:**
1. Lowercase + normalize text
2. Exact match against skill dictionary (O(n) lookup via set)
3. spaCy NER for PRODUCT/ORG entities (catches unlisted tools)
4. TF-IDF top-N keywords for importance scoring (scikit-learn)
5. Extract years of experience patterns via regex (`\d+\+?\s+years?`)

**Interface:**
```python
def extract_skills(text: str) -> list[ExtractedSkill]: ...
```

**Acceptance criteria:**
- Given a typical JD, extracts at least the explicitly mentioned tech stack
- No LLM calls
- Runs in < 2 seconds on CPU for a 2000-word document

---

#### Task 4.4 — Three-layer matching engine

**What to build:**  
`backend/app/services/matcher.py` — matches resume skills against JD skills.

**Three layers:**
1. **Exact match**: `resume_skill == jd_skill` (case-insensitive) → score 1.0
2. **Fuzzy match**: `rapidfuzz.fuzz.token_sort_ratio(a, b) >= 85` → score 0.85
3. **Semantic match**: only if layers 1+2 miss — use cosine similarity of TF-IDF vectors as fallback (avoid Ollama embedding calls in the hot path)

**Interface:**
```python
def match(resume_skills: list[str], jd_skills: list[str]) -> MatchResult: ...
```

**Acceptance criteria:**
- "JavaScript" vs "Javascript" → matched (exact after normalize)
- "Node.js" vs "NodeJS" → matched (fuzzy)
- "REST API" vs "RESTful services" → matched (fuzzy or semantic)
- "React" missing from resume → appears in missing_keywords
- Returns match percentage per category, not just overall

---

#### Task 4.5 — Weighted ATS scoring

**What to build:**  
`backend/app/services/ats_scorer.py` — combines layer outputs into final score.

**Weights:**
```
Skills match      = 40%
Experience match  = 30%  (years of exp, seniority keywords)
Keyword coverage  = 20%  (% of JD keywords found in resume)
Education match   = 10%  (degree keywords)
```

**Acceptance criteria:**
- Score is deterministic — same inputs always produce same score
- Score range: 0–100 (integer)
- No LLM involvement
- Returns breakdown dict with per-category scores alongside total

---

#### Task 4.6 — Analysis API endpoints

**What to build:**  
`backend/app/api/analysis.py`

**Endpoints:**
```
POST /api/analysis/match          — body: {application_id, resume_id}
POST /api/analysis/extract-skills — body: {text}
GET  /api/analysis/{application_id}/results — latest match result
```

**Acceptance criteria:**
- POST /match runs full pipeline, stores result in match_results, returns JSON
- Repeated POST /match for same (application_id, resume_id) updates existing record (upsert)
- GET /results returns stored result or 404

---

#### Task 4.7 — Frontend Analysis UI

**What to build:**  
Analysis tab on application detail page showing score + breakdown.

**Acceptance criteria:**
- "Run Analysis" button visible when application has a linked resume and a JD
- While running, shows spinner
- Result: circular gauge showing ATS score (0–100) with color (red < 40, yellow 40–70, green > 70)
- Two columns: "Matched Keywords" (green chips) and "Missing Keywords" (red chips)
- Per-category score breakdown (skills/experience/keyword coverage/education)
- "Re-run Analysis" option for stale results

---

**CHECKPOINT 4:** User uploads resume → pastes JD into application → clicks "Run Analysis" → sees ATS score + exact keyword gaps. No LLM used in this path.

---

### Phase 5 — AI Layer: Ollama Integration (Vertical Slice 4)

**Goal:** Interview prep generation + resume wording suggestions via local LLM.  
**Estimate:** 4–5 days  
**Depends on:** Phase 3 (resume text), Phase 4 (extracted skills)

#### Task 5.1 — ai_cache model + Ollama HTTP client

**What to build:**  
- `backend/app/models/ai_cache.py` — cache table (cache_key, prompt_hash, response JSON, created_at)
- `backend/app/ai/ollama_client.py` — thin async HTTP wrapper around `http://localhost:11434/api/generate`

**Ollama client spec:**
- POST to `/api/generate` with model, prompt, stream=False
- 120s timeout
- Returns raw text response
- Raises `OllamaUnavailableError` if Ollama not running (connection refused)
- Raises `OllamaTimeoutError` on timeout
- Both errors are caught at API layer and return 503

**Acceptance criteria:**
- `ollama_client.generate(model, prompt)` returns string response
- If Ollama is not running, raises `OllamaUnavailableError` (not crashes)
- Cache table created by `init_db()`

---

#### Task 5.2 — AI cache service

**What to build:**  
`backend/app/ai/cache.py` — hash-based cache lookup and store.

**Interface:**
```python
def get_cached(prompt_hash: str) -> str | None: ...
def store_cached(prompt_hash: str, cache_key: str, response: str) -> None: ...
def make_hash(prompt: str) -> str: ...  # SHA256
```

**Acceptance criteria:**
- Same prompt hash always returns same cached response
- Cache hit skips Ollama call entirely
- Cache entries never expire in MVP (manual clear only)

---

#### Task 5.3 — Interview prep prompt templates

**What to build:**  
`backend/app/ai/prompts/interview_prep.py` — versioned prompt template.

**Input context (preprocessed — NOT full resume):**
- role, company
- top 10 JD skills (from extractor)
- top 5 resume strengths (from matcher)
- missing skills list

**Output format (forced JSON):**
```json
{
  "technical_topics": [{"topic": "...", "priority": "high|medium|low", "why": "..."}],
  "behavioral_questions": ["..."],
  "coding_topics": ["..."],
  "study_roadmap": [{"week": 1, "focus": "...", "resources": [...]}]
}
```

**Safety constraints in prompt:**
```
Return ONLY valid JSON. No markdown. No prose.
Do not invent skills not present in the provided context.
Do not fabricate company-specific information.
```

**Acceptance criteria:**
- Prompt is < 500 tokens (preprocessed, not full JD)
- Response parsed as JSON without error for valid Ollama output
- Malformed JSON falls back gracefully (retry once, then return structured error)

---

#### Task 5.4 — Interview prep generation service + API

**What to build:**  
Service + endpoint wiring it together.

**Endpoint:** `POST /api/interview/generate` body: `{application_id}`

**Pipeline:**
1. Load application (JD + company + role)
2. Load linked resume (parsed_text)
3. Extract JD skills (reuse Task 4.3 extractor, cached in extracted_skills)
4. Identify top resume strengths (from match_results or re-run matcher)
5. Build short prompt (< 500 tokens)
6. Check ai_cache — return cached if hit
7. Call Ollama qwen2.5:7b
8. Parse JSON, store in interview_prep table + cache
9. Return structured response

**Acceptance criteria:**
- First call: Ollama generates response (may take 30–120s on CPU)
- Second identical call: returns from cache in < 100ms
- If Ollama not running: returns 503 with `{"error": "AI service unavailable", "detail": "..."}`
- Output always contains all 4 JSON keys (missing keys default to empty arrays)

---

#### Task 5.5 — Resume improvement suggestions API

**What to build:**  
`POST /api/analysis/improve-resume` 

**Input:** `{resume_id, application_id, bullet_text}`  
**Output:** `{original: "...", suggestion: "...", changes: ["added keyword X", ...]}`

**Safety prompt:**
```
Improve the wording of this resume bullet for the given job description context.
DO NOT invent new skills, projects, or experiences.
DO NOT add years of experience not mentioned.
Only rephrase and clarify what is already stated.
Return JSON only.
```

**Acceptance criteria:**
- LLM only improves wording — never adds new skills or invents experience
- Response always includes `original` field (unchanged input) for comparison
- Cached by hash of (bullet_text + application_id)

---

#### Task 5.6 — Frontend Interview Prep page

**What to build:**  
Interview prep view accessible from application detail page.

**Acceptance criteria:**
- "Generate Interview Prep" button on application detail (disabled if no JD)
- Shows loading state with message "Generating… this may take up to 2 minutes"
- Displays result in tabbed sections: Technical Topics, Behavioral Questions, Coding Topics, Study Roadmap
- Each technical topic shows priority badge (high/medium/low) and "why this matters" explanation
- "Regenerate" button clears cache and reruns
- Cached results load instantly with "From cache" label + timestamp

---

#### Task 5.7 — Frontend Resume Improvement panel

**What to build:**  
Side panel in Resume detail page for per-bullet improvement suggestions.

**Acceptance criteria:**
- User selects a bullet text from resume (textarea or pre-split bullets)
- "Improve Wording" button POSTs to /api/analysis/improve-resume
- Side-by-side diff view: original | suggested
- "Apply" copies suggestion to clipboard or inserts into editable field
- "Skip" dismisses without saving

---

**CHECKPOINT 5:** AI features end-to-end — generate interview prep from application, see cached results on second load, get wording suggestions for resume bullets. Ollama unavailability handled gracefully.

---

### Phase 6 — Dashboard Analytics (Vertical Slice 5)

**Goal:** Career analytics dashboard with charts from real application data.  
**Estimate:** 2–3 days  
**Depends on:** Phase 2 (applications data in DB)

#### Task 6.1 — Dashboard analytics service + API

**What to build:**  
`backend/app/services/dashboard.py` + `GET /api/dashboard/summary`

**Response structure:**
```json
{
  "totals": {
    "total": 42,
    "applied": 30,
    "interviewing": 8,
    "offers": 2,
    "rejected": 15,
    "pending_followups": 5
  },
  "rates": {
    "interview_rate": 0.27,
    "offer_rate": 0.07,
    "rejection_rate": 0.50
  },
  "monthly_trend": [
    {"month": "2026-01", "count": 8},
    ...
  ],
  "status_distribution": [
    {"status": "applied", "count": 30},
    ...
  ],
  "skill_demand": [
    {"skill": "Python", "count": 28},
    ...
  ]
}
```

**Acceptance criteria:**
- All counts computed via SQL aggregation (no Python loops over all rows)
- monthly_trend covers last 6 months
- skill_demand aggregated from all job descriptions using Task 4.3 extractor
- Endpoint responds in < 500ms for up to 500 applications

---

#### Task 6.2 — Frontend Dashboard page

**What to build:**  
Dashboard with KPI cards + three Recharts charts.

**Acceptance criteria:**
- 4 KPI cards: Total Applications, Interview Rate (%), Offer Rate (%), Pending Follow-ups
- Line chart: monthly applications (last 6 months) — Recharts LineChart
- Pie chart: status distribution — Recharts PieChart with legend
- Bar chart: top 10 skills in demand — Recharts BarChart (horizontal)
- All charts responsive (ResponsiveContainer)
- Empty state if < 3 applications ("Add more applications to see analytics")

---

**CHECKPOINT 6:** Dashboard shows live career analytics. All charts pull from real DB data.

---

### Phase 7 — Polish & Hardening

**Estimate:** 4–5 days  
**Depends on:** All phases complete

#### Task 7.1 — Alembic migrations

Replace `init_db()` create-all with proper Alembic migration chain.

**Acceptance criteria:**
- `alembic upgrade head` creates all tables from scratch on a fresh DB
- `alembic revision --autogenerate` detects schema changes correctly

---

#### Task 7.2 — SQLite FTS5 full-text search

Replace ILIKE queries in `applications` service with SQLite FTS5 virtual table.

**Acceptance criteria:**
- FTS5 virtual table `applications_fts` synced with `applications` table via triggers
- Search on company/title/notes/JD is faster and supports phrase queries

---

#### Task 7.3 — Dark mode

Tailwind `dark:` variants + Zustand theme store + toggle in sidebar.

**Acceptance criteria:**
- All pages readable in dark mode
- Theme preference persisted in localStorage

---

#### Task 7.4 — Export feature

`GET /api/applications/export?format=json|csv` + download button in UI.

**Acceptance criteria:**
- JSON export contains all non-deleted applications with all fields
- CSV export is spreadsheet-compatible (proper quoting for JD text)
- File downloads to user's Downloads folder via browser

---

#### Task 7.5 — Mobile responsiveness

Audit all pages at 375px width.

**Acceptance criteria:**
- Sidebar collapses to bottom tab bar on mobile
- Tables become card lists on mobile
- Forms are usable on a phone screen

---

**CHECKPOINT 7 (SHIP):** All 5 core features working, dark mode, mobile-friendly, exports working, migrations clean.

---

## What Deliberately Excluded (Per Design Doc)

These are explicitly out of scope until post-MVP:

- Multi-user auth (JWT, OAuth, Clerk)
- Real-time sync / WebSockets
- Browser extension / Chrome scraping
- Email integration
- Notifications system
- Vector database (ChromaDB, Pinecone)
- LangChain or agent frameworks
- Docker orchestration / Kubernetes
- Cloud deployment of Ollama
- Autonomous AI workflows

---

## Technology Gaps to Close Before Phase 3

Add to `backend/requirements.txt` and `environment.yml`:

```
pymupdf>=1.24.0
python-docx>=1.1.0
rapidfuzz>=3.9.0
spacy>=3.7.0
scikit-learn>=1.5.0
httpx>=0.27.0
alembic>=1.13.0
```

Post-install step: `python -m spacy download en_core_web_sm`

---

## Estimated Total Timeline (Part-Time Solo)

| Phase | Description | Estimate |
|-------|-------------|----------|
| P1 | Backend Foundation | ✅ Done |
| P2 | Applications Frontend | 3–4 days |
| P3 | Resume System | 3–4 days |
| P4 | ATS Matching Engine | 4–5 days |
| P5 | Ollama AI Layer | 4–5 days |
| P6 | Dashboard | 2–3 days |
| P7 | Polish & Hardening | 4–5 days |
| **Total** | | **~5–6 weeks** |
