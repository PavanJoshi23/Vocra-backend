# Vocra — Task List

> See `tasks/plan.md` for full acceptance criteria, dependency graph, and architectural notes.

---

## Phase 1 — Backend Foundation ✅ COMPLETE

- [x] FastAPI app + CORS + lifespan hook
- [x] SQLite + SQLAlchemy 2.0 session management
- [x] Application model (all fields + soft delete)
- [x] Applications CRUD API (list/search/filter, create, get, update, soft-delete)
- [x] Pydantic v2 schemas
- [x] `GET /api/health` endpoint
- [x] Storage directory structure (resumes/exports/backups)
- [x] Conda environment + requirements.txt

**CHECKPOINT 1 ✅ — Backend API running at localhost:8000**

---

## Phase 2 — Applications Frontend (Vertical Slice 1)

- [x] **2.1** Scaffold React + Vite + JavaScript + Tailwind + shadcn/ui in `frontend/`
- [x] **2.2** App shell: sidebar layout + React Router routes (5 stub pages)
- [x] **2.3** API client + TanStack Query provider + typed application hooks
- [x] **2.4** Applications list page: table, search (debounced), status filter, empty state
- [x] **2.5** Create/Edit application modal: React Hook Form + Zod, all fields, inline validation
- [x] **2.6** Application detail page: full view, inline status update, delete with confirmation

**CHECKPOINT 2 ✅ — Full Applications CRUD working in browser**

---

## Phase 3 — Resume System (Vertical Slice 2)

- [x] **3.1** Resume SQLAlchemy model + update `init_db()` to create `resumes` table
- [x] **3.2** Add pymupdf, python-docx, rapidfuzz to requirements.txt + environment.yml
- [x] **3.3** Resume text extraction service (`backend/app/parsers/resume_parser.py`)
- [x] **3.4** Resume upload + list + detail + delete API (`POST /api/resumes/upload`, `GET /api/resumes`, etc.)
- [x] **3.5** Frontend Resume management page: file dropzone, upload progress, resume list cards
- [x] **3.6** Link resume to application: dropdown in Create/Edit form, display on detail page

**CHECKPOINT 3 ✅ — Upload PDF/DOCX → text extracted → linked to application**

---

## Phase 4 — ATS Matching Engine (Vertical Slice 3)

- [x] **4.1** Add spaCy, scikit-learn to deps + create tech skill keyword dictionary
- [x] **4.2** `extracted_skills` and `match_results` SQLAlchemy models
- [x] **4.3** Deterministic keyword extraction service (dict + spaCy NER + TF-IDF)
- [x] **4.4** Three-layer matching engine: exact → fuzzy (rapidfuzz) → semantic (TF-IDF cosine)
- [x] **4.5** Weighted ATS scoring (40% skills / 30% experience / 20% keyword coverage / 10% education)
- [x] **4.6** Analysis API: `POST /api/analysis/match`, `POST /api/analysis/extract-skills`, `GET /api/analysis/{id}/results`
- [x] **4.7** Frontend Analysis UI: "Run Analysis" button, ATS score gauge, matched/missing keyword chips, per-category breakdown

**CHECKPOINT 4 ✅ — Upload resume + paste JD → click Analyze → see ATS score + keyword gaps**

---

## Phase 5 — Ollama AI Layer (Vertical Slice 4)

- [x] **5.1** `ai_cache` model + Ollama HTTP client with timeout + error handling
- [x] **5.2** AI cache service: SHA256 hash → store/retrieve cached responses
- [x] **5.3** Interview prep prompt template (versioned, < 500 tokens, forced JSON output)
- [x] **5.4** Interview prep generation service + `POST /api/interview/generate` endpoint
- [x] **5.5** Resume improvement suggestions: `POST /api/analysis/improve-resume` (wording only, no hallucination)
- [x] **5.6** Frontend Interview Prep page: generate button, loading state, tabbed results, cached indicator
- [x] **5.7** Frontend Resume Improvement panel: bullet selector, side-by-side diff view, apply/skip

**CHECKPOINT 5 ✅ — AI interview prep works + caches + degrades gracefully if Ollama unavailable**

---

## Phase 6 — Dashboard Analytics (Vertical Slice 5)

- [x] **6.1** Dashboard analytics service + `GET /api/dashboard/summary` (SQL aggregations only)
- [x] **6.2** Frontend Dashboard: 4 KPI cards + Line chart + Pie chart + Bar chart (Recharts)

**CHECKPOINT 6 ✅ — Dashboard shows real analytics from application data**

---

## Phase 7 — Polish & Hardening ✅ COMPLETE

- [x] **7.1** Alembic migrations: replace `init_db()` create-all with proper migration chain
- [x] **7.2** SQLite FTS5 full-text search: replace ILIKE with FTS5 virtual table + triggers
- [x] **7.3** Dark mode: CSS `.dark` class variables + Zustand theme store + sidebar toggle
- [x] **7.4** Export feature: `GET /api/applications/export?format=json|csv` + download button
- [x] **7.5** Mobile responsiveness: sidebar → bottom tab bar, tables → cards at mobile width

**CHECKPOINT 7 ✅ (SHIP) — All features working, dark mode, mobile, exports, clean migrations**

---

## Dependency Reference

```
P1 ✅ → P2 (frontend can start now)
P1 ✅ → P3 (resume backend)
P3 → P4 (need resume text for matching)
P3 → P5 (need resume text for AI suggestions)
P4 → P5 (need extracted skills for interview prep context)
P2 → P3 UI, P4 UI, P5 UI, P6 UI (need app shell)
P1 → P6 (need applications data)
P1–P6 → P7 (polish after features complete)
```
