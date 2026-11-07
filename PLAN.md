# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

rust-issue-tracker

## Roadmap

### project-skeleton — Project skeleton with FastAPI backend and React frontend

Status: done

Acceptance:
- FastAPI app runs on localhost:8000
- React + Vite + TypeScript app runs on localhost:5173
- Docker compose brings up backend, frontend, Keycloak, PostgreSQL
- Basic health endpoints respond
- Backend tests pass (pytest)
- Frontend typecheck and build pass

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/models/__init__.py`, `backend/app/models/issue.py`, `backend/app/models/user.py`, `backend/app/api/__init__.py`, `backend/app/api/issues.py`, `backend/app/api/auth.py`, `backend/app/api/llm.py`, `backend/app/schemas/__init__.py`, `backend/app/schemas/issues.py`, `backend/app/schemas/auth.py`, `backend/app/schemas/llm.py`, `backend/app/services/__init__.py`, `backend/app/services/analysis.py`, `backend/app/services/github_sync.py`, `backend/app/services/llm.py`, `backend/requirements.txt`, `backend/Dockerfile`, `frontend/package.json`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/vite.config.ts`, `frontend/index.html`, `frontend/nginx.conf`, `frontend/Dockerfile`, `compose.yaml`, `docs/architecture.md`

Tests: `backend/tests/conftest.py`, `backend/tests/test_health.py`, `backend/tests/test_issues.py`, `backend/tests/test_analysis.py`, `backend/tests/test_auth.py`, `backend/tests/test_github_sync.py`, `backend/tests/test_llm.py`, `frontend/src/__tests__/setup.ts`, `frontend/src/__tests__/App.test.tsx`

### auth-oidc — OIDC authentication with Keycloak (PKCE flow)

Status: done

Acceptance:
- Login redirects to Keycloak
- Callback exchanges code for tokens
- Access token used for authenticated API calls
- Logout clears session
- Role-based access control (viewer, operator, admin)
- Tests cover unauthenticated rejection and role denial

Implementation: `backend/app/api/auth.py`, `backend/app/core/auth.py`, `backend/app/models/user.py`, `frontend/src/api/auth.ts`, `frontend/src/components/Login.tsx`, `frontend/src/contexts/AuthContext.tsx`, `frontend/src/pages/Callback.tsx`

Tests: `backend/tests/test_auth.py`, `frontend/src/__tests__/AuthContext.test.tsx`

### rust-issue-tracker — Rust tracking issue ingestion and storage

Status: done

Acceptance:
- GitHub API fetches tracking issues from rust-lang/rust
- Issues stored in SQLite with full metadata
- API endpoints for listing, filtering, searching issues
- Pagination and sorting support
- Background sync job updates issues periodically
- Manual sync trigger endpoint (POST /api/v1/issues/sync)
- Sync history endpoint (GET /api/v1/issues/sync/history)

Implementation: `backend/app/models/issue.py`, `backend/app/services/github_sync.py`, `backend/app/api/issues.py`, `backend/app/core/database.py`, `backend/app/main.py`, `backend/app/core/config.py`, `backend/requirements.txt`

Tests: `backend/tests/test_issues.py`, `backend/tests/test_github_sync.py`

### sync-endpoints — Manual sync trigger and history endpoints

Status: done

Acceptance:
- POST /api/v1/issues/sync triggers manual GitHub sync with max_pages parameter
- GET /api/v1/issues/sync/history returns recent sync operation logs
- Both endpoints require authentication (401 if unauthenticated)
- Sync response includes issues_fetched, issues_created, issues_updated, status, timestamps
- Tests cover unauthenticated rejection for both endpoints

Implementation: `backend/app/api/issues.py`

Tests: `backend/tests/test_issues.py`

### feature-analysis-engine — Feature stabilization analysis engine (core domain)

Status: planned

Acceptance:
- Parses tracking issue checklists and progress
- Calculates stabilization readiness score (0-100)
- Identifies blocking dependencies between features
- Extracts unresolved questions and categorizes them
- Deterministic algorithm, no LLM required
- API endpoint returns analysis for each issue

Implementation: `backend/app/services/analysis.py`, `backend/app/api/analysis.py`, `backend/app/models/analysis.py`

Tests: `backend/tests/test_analysis.py`

### llm-insights — Optional LLM-powered insights and summaries

Status: planned

Acceptance:
- Configurable LLM provider (OpenAI-compatible, Anthropic, Gemini, Ollama)
- Generates human-readable feature summaries
- Explains technical blockers in plain language
- Advisory only, clearly labeled, grounded in actual data
- Graceful degradation when LLM unavailable

Implementation: `backend/app/services/llm.py`, `backend/app/api/llm.py`, `backend/app/core/providers.py`

Tests: `backend/tests/test_llm.py`

### frontend-dashboard — React dashboard with three complete workflows

Status: planned

Acceptance:
- Workflow 1: Browse and search tracking issues with filters
- Workflow 2: View detailed analysis for a feature
- Workflow 3: Compare stabilization progress across features
- Loading, error, empty states for all views
- Responsive professional UI
- Typed API client derived from backend routes

Implementation: `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/IssueDetail.tsx`, `frontend/src/pages/Comparison.tsx`, `frontend/src/components/IssueList.tsx`, `frontend/src/components/AnalysisView.tsx`, `frontend/src/api/client.ts`

Tests: `frontend/src/__tests__/Dashboard.test.tsx`, `frontend/src/__tests__/IssueDetail.test.tsx`

### docs-and-polish — Documentation, packaging, and final polish

Status: planned

Acceptance:
- README with install/run/test steps, architecture diagram
- CHANGELOG.md with actual changes
- portfolio.json with correct metadata
- LICENSE (MIT)
- .env.example with blank credentials
- All CI checks pass
- Source code within 50-150 KB budget

Implementation: `README.md`, `CHANGELOG.md`, `portfolio.json`, `LICENSE`, `pyproject.toml`, `.env.example`, `docs/architecture.md`

---

Alan Vo · [alanvo.net](https://alanvo.net)
