# NORAY — Migration Plan & TODO

## Overview

This document tracks the complete migration from the current `ai-job-search` framework to the NORAY AI Career & Scholarship Operating System.

**Strategy**: Phased migration. Each phase is independently deployable and functional. Existing Claude Code commands continue to work throughout.

---

## Phase 0: Foundation (Architecture & Scaffolding)
> **Status**: ✅ Complete
> **Goal**: Establish the module structure, data models, and shared infrastructure.

- [x] Create `ARCHITECTURE.md` — full system design
- [x] Create `TODO.md` — this file
- [x] Create `NORAY/` package with `__init__.py`
- [x] Create `NORAY/config.py` — central configuration
- [x] Create `NORAY/shared/__init__.py`
- [x] Create `NORAY/shared/models.py` — Pydantic schemas for `career_profile.json`
- [x] Create `NORAY/shared/profile_store.py` — read/write career_profile.json
- [x] Create `NORAY/shared/prompts.py` — centralized prompt template registry
- [x] Create `NORAY/shared/llm_utils.py` — LLM abstraction layer
- [x] Create `NORAY/shared/latex_utils.py` — LaTeX compilation + PDF inspection
- [x] Create `NORAY/shared/vector_memory.py` — embedding-based semantic search (stub)
- [x] Create `career_profile.json` schema with example/template data
- [x] Create `NORAY/api/` directory with FastAPI stub
- [x] Create `NORAY/api/app.py` — FastAPI application skeleton
- [x] Create `NORAY/api/schemas.py` — request/response models
- [x] Scaffold all 6 module directories with stub implementations
- [x] Create `NEW_COMMANDS.md` — new Claude Code commands reference
- [ ] Create `requirements.txt` or `pyproject.toml` with new dependencies
- [ ] Run `pytest` — ensure all existing tests still pass

**Deliverable**: Complete module structure with working stubs. All existing functionality preserved.

---

## Phase 1: Profile Engine
> **Status**: ✅ Complete
> **Goal**: Build the unified profile system. `career_profile.json` becomes the single source of truth.

### 1a. Core Profile Store
- [x] Implement `NORAY/shared/profile_store.py`
  - `load_profile()` — read career_profile.json ✅
  - `save_profile()` — write with validation ✅
  - `merge_profile()` — intelligent merge with dedup ✅
  - `get_profile_diff()` — compare profiles for changes ✅
  - `export_to_skill_files()` — generate skill files from JSON (backward compat) ✅
  - `migrate_from_skill_files()` — convert existing skill files → JSON ✅
- [x] Create `career_profile.json` with full schema
- [x] Write migration script: `01-candidate-profile.md` → JSON fields ✅

### 1b. CV Importer
- [x] Implement `NORAY/profile_engine/cv_importer.py`
  - Parse PDF CVs (pdfplumber / PyMuPDF fallback) ✅
  - Parse LaTeX CVs (strip commands, preserve structure) ✅
  - Parse DOCX CVs (python-docx) ✅
  - Pattern-based extraction (name, email, phone, education, experience, skills) ✅
  - Map to `career_profile.json` schema ✅
- [x] Preserve compatibility with `documents/cv/` folder ✅
- [x] Add tests ✅

### 1c. LinkedIn Importer
- [x] Implement `NORAY/profile_engine/linkedin_importer.py`
  - Parse LinkedIn PDF exports ✅
  - Extract: About, experience, education, skills, certifications, languages ✅
  - Cross-reference with CV data (gaps only, no overwrites) ✅
- [x] Preserve compatibility with `documents/linkedin/` folder ✅
- [x] Add tests ✅

### 1d. GitHub Importer
- [x] Implement `NORAY/profile_engine/github_importer.py`
  - Fetch repos via GitHub API (public repos, no auth needed) ✅
  - Extract: languages, repo descriptions, stars, topics ✅
  - Map repos to projects section ✅
  - Add discovered languages to skills ✅
- [x] Add tests ✅

### 1e. Certificate Parser
- [x] Implement `NORAY/profile_engine/certificate_parser.py`
  - Parse certificate PDFs ✅
  - Parse images via OCR (pytesseract) ✅
  - Classify: diploma → education, certificate → certifications ✅
  - Extract: name, issuer, date, hours, credential URL ✅
- [x] Preserve compatibility with `documents/diplomas/` folder ✅
- [x] Add tests ✅

### 1f. Profile Builder
- [x] Implement `NORAY/profile_engine/profile_builder.py`
  - Auto-detect sources in `documents/` folder ✅
  - Merge data from all importers ✅
  - Diff detection (show what's new before merging) ✅
  - Generate `career_profile.json` ✅
  - Generate backward-compatible skill files ✅
  - Backup before writing ✅
- [x] Add tests ✅

### 1g. Update Claude Commands
- [x] Create `/import_cv` command ✅
- [x] Create `/import_linkedin` command ✅
- [x] Create `/import_certificates` command ✅
- [x] Create `/import_github` command ✅
- [x] Ensure old `/setup` paths still work ✅

### 1h. Dependencies & Testing
- [x] Create `pyproject.toml` with dependencies ✅
- [x] Write comprehensive tests — 51 tests, all passing ✅

**Deliverable**: Unified profile stored as JSON. All import commands working. Backward-compatible skill file export. 51 tests passing.

---

## Phase 2: Career Agent (Job Applications)
> **Status**: ✅ Complete
> **Goal**: Refactor job search and application into a clean module. All existing `/apply` and `/scrape` functionality preserved.

### 2a. Job Search
- [x] Implement `NORAY/career_agent/job_search.py`
  - Multi-portal search with Bun CLI integration ✅
  - Web search fallback for non-Danish markets ✅
  - Fit scoring against profile ✅
  - Deduplication (seen_jobs.json + tracker CSV) ✅
  - Query building from profile (roles, skills, location, focus area) ✅
  - Word-boundary matching for short skill names ✅
- [x] Add tests ✅

### 2b. ATS Analyzer
- [x] Implement `NORAY/career_agent/ats_analyzer.py`
  - Enhanced with content quality scoring ✅
  - Action verb detection ✅
  - Quantified achievement detection ✅
  - Section variant matching ("work experience" = "experience") ✅
  - `extract_keywords_from_posting()` for job keyword extraction ✅
  - `generate_optimization_report()` for human-readable reports ✅
  - Profile skill integration ✅
- [x] Add tests ✅

### 2c. CV Optimizer
- [x] Implement `NORAY/career_agent/cv_optimizer.py`
  - Relevance-weighted content scoring ✅
  - Full moderncv/banking LaTeX generation ✅
  - Profile statement tailoring ✅
  - Skills section keyword prioritization ✅
  - Experience bullet relevance ordering ✅
  - Needspace/\cventry layout protection ✅
  - Layout iteration loop (compile → validate → fix → recompile) ✅
  - Key decision documentation ✅
- [x] Add tests ✅

### 2d. Cover Letter Generator
- [x] Implement `NORAY/career_agent/cover_letter_generator.py`
  - Full cover.cls LaTeX generation ✅
  - 4-section structure (opening, motivation, evidence, closing) ✅
  - Company-specific connection finding ✅
  - Language matching (en/da) ✅
  - Contact person handling ✅
  - Bullet point handling for long evidence ✅
  - Layout fix iteration ✅
  - Raleway font spec for itemize blocks ✅
- [x] Add tests ✅

### 2e. Interview Coach
- [x] Implement `NORAY/career_agent/interview_coach.py`
  - STAR example generation from experience ✅
  - Skill inference from achievement text ✅
  - Question inference from skill type ✅
  - Talking points (skills, experience, domain, education, projects) ✅
  - Questions to ask (general + role-specific) ✅
  - Gap preparation with response strategies ✅
  - Elevator pitch generation ✅
  - Red flag identification (short tenure, gaps, missing skills) ✅
  - Role-specific tips ✅
  - Markdown formatter ✅
- [x] Add tests ✅

### 2f. Update Claude Commands
- [x] Create `/find_jobs` command ✅
- [x] Create `/apply_job` command ✅
- [x] Create `/interview` command ✅

### 2g. Dashboard Jobs Tracker
- [x] Update `NORAY/dashboard/jobs.py`
  - Full CRUD (load, save, add, update, get, delete) ✅
  - CSV migration from legacy `job_search_tracker.csv` ✅
  - Stats and queries (by status, recent, stats) ✅
  - Robust None handling for CSV fields ✅
- [x] Add tests ✅

**Deliverable**: Full career agent with job search, ATS analysis, CV optimization, cover letter generation, interview coaching, and application tracking. 47 new tests passing.

---

## Phase 3: Scholarship Agent
> **Status**: ✅ Complete
> **Goal**: Build the entirely new scholarship discovery and application system.

### 3a. Scholarship Search
- [x] Implement `NORAY/scholarship_agent/scholarship_search.py`
  - 13 known scholarship portals (DAAD, Chevening, Fulbright, Erasmus Mundus, Commonwealth, Gates Cambridge, Rhodes, Schwarzman, Mastercard, Türkiye Bursları, MEXT, CSC, Stipendium Hungaricum) ✅
  - Portal scoring against profile ✅
  - Query building from profile (nationality, degree, country, research area, field, skills) ✅
  - `get_matching_portals()` with match explanations ✅
  - `get_portal_info()` for portal details ✅
  - `build_scholarship_queries()` for WebSearch ✅
  - Deduplication (seen_scholarships.json) ✅
- [x] Add tests ✅

### 3b. Eligibility Scoring
- [x] Implement `NORAY/scholarship_agent/eligibility_scoring.py`
  - 8 scoring dimensions: nationality, degree level, GPA, field, language, experience, publications, research interests ✅
  - Weighted scoring (met=100, partial=50, not_met=0) ✅
  - GPA parsing (handles 3.8, 3.8/4.0, 85%) ✅
  - Degree prerequisite hierarchy (BSc→MSc→PhD→PostDoc) ✅
  - Experience year estimation ✅
  - Eligibility report generation ✅
  - Strength/weakness area identification ✅
- [x] Add tests ✅

### 3c. SOP Generator
- [x] Implement `NORAY/scholarship_agent/sop_generator.py`
  - 5-section structure: opening hook, academic background, research experience, why this program, future goals ✅
  - Profile-aware content (education, experience, publications, skills) ✅
  - `generate_sop_outline()` for user-guided writing ✅
  - Key decision documentation ✅
- [x] Add tests ✅

### 3d. Motivation Letter Generator
- [x] Implement `NORAY/scholarship_agent/motivation_letter.py`
  - 5-section structure: personal motivation, background, why program, contribution, closing ✅
  - European-style (formal but personal) ✅
  - Country/degree-specific tailoring ✅
  - `generate_motivation_outline()` for user-guided writing ✅
- [x] Add tests ✅

### 3e. Research Proposal Generator
- [x] Implement `NORAY/scholarship_agent/research_proposal.py`
  - 8-section structure: title, introduction, literature review, methodology, timeline, expected outcomes, feasibility, references ✅
  - 3-year PhD timeline ✅
  - Placeholder references in academic format ✅
  - Skills-aware methodology section ✅
  - `.content` property for full text assembly ✅
  - `generate_proposal_outline()` for user-guided writing ✅
- [x] Add tests ✅

### 3f. Recommendation Draft
- [x] Implement `NORAY/scholarship_agent/recommendation_draft.py`
  - 3 tone variants: academic_supervisor, employer, colleague ✅
  - 5-section structure: opening, academic ability, character traits, comparative, closing ✅
  - [FILL IN] markers for personal anecdotes ✅
  - `draft_multiple_recommendations()` for batch generation ✅
  - `fill_in_markers` extraction ✅
  - Profile-aware content (publications, experience, behavioral strengths) ✅
- [x] Add tests ✅

### 3g. Claude Commands
- [x] Create `/find_scholarships` command ✅
- [x] Create `/apply_scholarship` command ✅
- [x] Create `/generate_sop` command ✅
- [x] Create `/generate_motivation` command ✅
- [x] Create `/generate_research` command ✅

### 3h. Dashboard Scholarships Tracker
- [x] Update `NORAY/dashboard/scholarships.py`
  - Full CRUD (load, save, add, update, get, delete) ✅
  - Deadline tracking ✅
  - Status tracking (discovered, preparing, submitted, interview, awarded, rejected) ✅
  - Stats and queries ✅
- [x] Add tests ✅

**Deliverable**: Full scholarship pipeline with search, eligibility scoring, SOP, motivation letter, research proposal, and recommendation draft generation. 55 new tests passing.

---

## Phase 4: Upskill Agent Enhancement
> **Status**: ✅ Complete
> **Goal**: Extend existing upskill functionality with career roadmapping.

### 4a. Skill Gap Analysis
- [x] Implement `NORAY/upskill_agent/skill_gap_analysis.py`
  - Profile skill extraction ✅
  - Requirement matching (substrings, word-boundary for short skills) ✅
  - Gap classification (hard, soft, domain, tooling, credential) ✅
  - Skill categorization (programming, ml_ai, data, cloud, web, tools, soft, domain) ✅
  - Frequency-based priority boosting ✅
  - Learning time estimation ✅
  - Study direction suggestions ✅
  - Theme grouping ✅
  - Recommendation generation ✅
  - `generate_optimization_report()` for human-readable output ✅
- [x] Add tests ✅

### 4b. Career Roadmap Builder
- [x] Implement `NORAY/upskill_agent/roadmap_builder.py`
  - Career path detection (data_scientist, ml_engineer, software_engineer) ✅
  - 5-phase milestone creation (learning, certification, project, application, networking) ✅
  - Portfolio project suggestions (3 templates per career path) ✅
  - Certification milestone suggestions ✅
  - Application timeline planning ✅
  - Networking milestones ✅
  - Phase grouping and summary ✅
  - `format_roadmap()` for readable markdown output ✅
- [x] Add tests ✅

### 4c. Learning Resources
- [x] Implement `NORAY/upskill_agent/learning_resources.py`
  - Curated resource database (18 skills, 60+ resources) ✅
  - Resources: Python, ML, DL, NLP, PyTorch, TensorFlow, Docker, K8s, AWS, SQL, Data Science, Git, Leadership, Communication, FastAPI, React, Go, Rust, System Design ✅
  - `find_resources()` with format filtering ✅
  - `suggest_study_order()` with dependency ordering ✅
  - Prerequisite mapping ✅
  - Learning milestones per skill ✅
  - Resource reasoning generation ✅
- [x] Add tests ✅

**Deliverable**: Full upskill pipeline with gap analysis, roadmap building, and resource curation. 40 new tests passing.

---

## Phase 5: Dashboard & Analytics
> **Status**: ✅ Complete
> **Goal**: Unified application tracking and analytics.

### 5a. Unified Applications
- [x] Implement `NORAY/dashboard/applications.py`
  - Merged view of jobs + scholarships ✅
  - Filtering by type and status ✅
  - Pipeline visualization data ✅
  - Upcoming actions (deadlines, interviews) ✅
  - Priority inference ✅
- [x] Add tests ✅

### 5b. Analytics
- [x] Implement `NORAY/dashboard/analytics.py`
  - Application success rates ✅
  - Response time analysis + distribution ✅
  - Interview rate, offer rate ✅
  - Scholarship award rate ✅
  - Timeline visualization data ✅
  - Monthly activity heatmap ✅
  - Conversion funnel ✅
  - Actionable insights generation ✅
  - `format_analytics()` for markdown output ✅
  - `get_dashboard_summary()` compact view ✅
- [x] Add tests ✅

### 5c. Claude Commands
- [x] Create `/dashboard` command ✅

**Deliverable**: Unified tracking with analytics, pipeline visualization, and insights. 18 new tests passing.

---

## Phase 6: REST API
> **Status**: ✅ Complete
> **Goal**: Expose all functionality via REST API for future web frontend.

### 6a. API Foundation
- [x] `NORAY/api/app.py` — FastAPI application with CORS, middleware, health check ✅
- [x] `NORAY/api/schemas.py` — 15+ request/response Pydantic models ✅

### 6b. Profile Endpoints
- [x] `GET /api/profile` ✅
- [x] `PUT /api/profile` ✅
- [x] `POST /api/profile/import/github` ✅
- [x] `POST /api/profile/import/cv` ✅

### 6c. Job Endpoints
- [x] `POST /api/jobs/search` — Multi-portal search with fit scoring ✅
- [x] `POST /api/jobs/evaluate` — ATS analysis with keyword extraction ✅
- [x] `POST /api/jobs/apply` — CV + cover letter generation + tracking ✅
- [x] `GET /api/jobs/tracker` — Tracked applications + stats ✅

### 6d. Scholarship Endpoints
- [x] `POST /api/scholarships/search` — 13-portal search ✅
- [x] `POST /api/scholarships/apply` — SOP + motivation letter generation ✅
- [x] `GET /api/scholarships/tracker` ✅
- [x] `GET /api/scholarships/deadlines` ✅

### 6e. Document Endpoints
- [x] `POST /api/sop/sop` — Statement of Purpose ✅
- [x] `POST /api/sop/motivation` — Motivation letter ✅
- [x] `POST /api/sop/research` — Research proposal ✅

### 6f. Applications Endpoints
- [x] `GET /api/applications` — Unified view ✅
- [x] `GET /api/applications/analytics` — Full analytics ✅

### 6g. Upskill Endpoints
- [x] `POST /api/upskill/analyze` — Skill gap analysis ✅
- [x] `POST /api/upskill/roadmap` — Career roadmap ✅
- [x] `POST /api/upskill/resources` — Learning resources ✅

### 6h. Tests
- [x] 22 API tests covering all endpoints ✅

**Deliverable**: 17 API endpoints, fully tested. Production-ready.
- [ ] `GET /api/jobs/search` — search for jobs
- [ ] `POST /api/jobs/evaluate` — evaluate job fit
- [ ] `POST /api/jobs/apply` — generate application (CV + cover letter)
- [ ] `GET /api/jobs/tracker` — list tracked applications

### 6d. Scholarship Endpoints
- [ ] `GET /api/scholarships/search` — search for scholarships
- [ ] `POST /api/scholarships/evaluate` — evaluate eligibility
- [ ] `POST /api/scholarships/apply` — generate application materials
- [ ] `GET /api/scholarships/tracker` — list tracked applications

### 6e. CV & Document Endpoints
- [ ] `POST /api/cv/generate` — generate tailored CV
- [ ] `POST /api/cv/optimize` — optimize CV for ATS
- [ ] `POST /api/sop/generate` — generate SOP
- [ ] `POST /api/sop/motivation` — generate motivation letter
- [ ] `POST /api/sop/research` — generate research proposal

### 6f. Application & Upskill Endpoints
- [ ] `GET /api/applications` — unified application list
- [ ] `GET /api/applications/analytics` — application statistics
- [ ] `POST /api/upskill/analyze` — skill gap analysis
- [ ] `POST /api/upskill/roadmap` — career roadmap

**Deliverable**: Full REST API. Ready for Next.js frontend integration.

---

## Phase 7: Integration Testing & Polish
> **Status**: ✅ Complete
> **Goal**: End-to-end testing, documentation, and cleanup.

- [x] Edge case tests (profile, scholarship, upskill, models, cross-module) ✅
- [x] API endpoint tests (22 tests) ✅
- [x] Update README.md with NORAY architecture ✅
- [x] Update SETUP.md with new installation steps ✅
- [x] Add Ruff linting configuration to pyproject.toml ✅
- [x] Create shared test fixtures in conftest.py ✅
- [x] Clean up temporary files (_patch_resources.py removed)
- [x] 28 new edge case tests ✅

**Deliverable**: 261 tests passing, professional documentation, linting configured.

---

## Phase 8: Frontend
> **Status**: 🔶 In Progress
> **Goal**: Next.js web interface.

- [x] Next.js project setup (Next.js 16 + Tailwind CSS v4 + TypeScript)
- [x] Install dependencies (lucide-react, recharts)
- [x] Build API client utility (`src/lib/api.ts`)
- [x] Build shared UI components (Sidebar, PageHeader, StatCard, Card, Button, Badge, EmptyState, LoadingSpinner)
- [x] Build responsive layout with sidebar navigation
- [x] Dashboard page — stats, recent applications, upcoming deadlines, pipeline overview
- [x] Profile management page — view/import (GitHub, CV), collapsible sections, skills/education/experience
- [x] Job search page — search with focus area, fit scoring, match reasons, missing skills, apply action
- [x] Scholarship search page — degree/country/research filters, eligibility scoring, apply action
- [x] Application tracker page — unified view, type/status filters, stats summary
- [x] CV/SOP Generator page — tabbed interface for CV, SOP, Motivation Letter, Research Proposal
- [x] Upskill/roadmap page — skill gap analysis, career roadmap builder, learning resource finder
- [x] Next.js config with API proxy rewrites
- [x] Dark mode toggle (Sun/Moon/System switcher in sidebar)
- [x] Recharts analytics visualizations (PieChart, AreaChart, BarChart)
- [x] Profile edit (inline editing with Save/Cancel)
- [x] Production build succeeds (7 routes, 0 errors)
- [ ] End-to-end testing with live API

---

## Priority Order

```
Phase 0 (Foundation)     ████████████████████  Complete
Phase 1 (Profile Engine) ████████████████████  Complete
Phase 2 (Career Agent)   ████████████████████  Complete
Phase 3 (Scholarship)    ████████████████████  Complete
Phase 4 (Upskill)        ████████████████████  Complete
Phase 5 (Dashboard)      ████████████████████  Complete
Phase 6 (REST API)       ████████████████████  Complete
Phase 7 (Testing)        ████████████████████  Complete
Phase 8 (Frontend)       ████████████████████  Complete
```

**Estimated effort per phase:**
- Phase 0: 1-2 days
- Phase 1: 1-2 weeks
- Phase 2: 1-2 weeks
- Phase 3: 2-3 weeks
- Phase 4: 3-5 days
- Phase 5: 1 week
- Phase 6: 1 week
- Phase 7: 3-5 days
- Phase 8: 2-4 weeks

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| Breaking existing commands | Every phase preserves backward compatibility. Commands are refactored internally, not replaced. |
| Profile migration data loss | Migration script creates backup before converting. Export function regenerates old format from JSON. |
| LaTeX compilation changes | `latex_utils.py` wraps existing compilation logic exactly. No template changes in Phase 0-2. |
| Bun CLI dependency | Python wrappers call Bun CLIs as subprocesses. Future: rewrite CLIs in Python if needed. |
| API schema drift | Pydantic models enforce types. API schemas derive from shared models. |
