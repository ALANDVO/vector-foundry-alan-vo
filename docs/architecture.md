# Vector Foundry - Architecture Documentation

## System Overview

Vector Foundry is a full-stack application for tracking and analyzing Rust compiler feature stabilization progress. It consists of a FastAPI backend, React frontend, Keycloak for authentication, and PostgreSQL/SQLite for persistence.

## Components

### Backend (FastAPI)

**Entry Point**: `backend/app/main.py`
- FastAPI application with lifespan management
- CORS middleware configured for frontend origin
- Health endpoints: `/health`, `/health/ready`
- API version prefix: `/api/v1`

**Modules**:
- `app/api/issues.py` — REST endpoints for issue listing, detail, comparison
- `app/api/auth.py` — OIDC authentication with Keycloak (login, callback, logout, user info)
- `app/api/llm.py` — Optional LLM-powered insights (summary, blocker explanation)
- `app/core/config.py` — Pydantic Settings for environment-based configuration
- `app/core/database.py` — SQLAlchemy async setup with SQLite/PostgreSQL support
- `app/models/issue.py` — TrackingIssue, ChecklistItem, IssueAnalysis, SyncLog
- `app/models/user.py` — User, AuditLog
- `app/schemas/` — Pydantic models for request/response validation
- `app/services/analysis.py` — **Core domain engine**: deterministic stabilization analysis
- `app/services/github_sync.py` — GitHub API ingestion service
- `app/services/llm.py` — Multi-provider LLM abstraction (OpenAI, Anthropic, Gemini, Ollama)

### Frontend (React + TypeScript + Vite)

**Entry Point**: `frontend/src/main.tsx`
- React 18 with React Router v6
- AuthContext for session management (tokens in sessionStorage)
- Typed API client derived from backend routes

**Pages**:
- `Dashboard.tsx` — Issue list with search, filter, sort, pagination
- `IssueDetail.tsx` — Full issue view with checklist, analysis, readiness visualization
- `Comparison.tsx` — Side-by-side comparison of up to 6 issues

**Components**:
- `Layout.tsx` — Header with navigation, user menu, logout
- `Login.tsx` — Keycloak login entry point
- `index.css` — Design system with CSS custom properties

### Authentication

**Flow**: Authorization Code with PKCE
1. Frontend redirects to `/api/v1/auth/login?redirect=/`
2. Backend redirects to Keycloak authorization endpoint
3. Keycloak redirects back to `/api/v1/auth/callback` with code
4. Backend exchanges code for tokens at Keycloak token endpoint
5. Backend redirects to frontend with tokens in URL fragment
6. Frontend stores tokens in sessionStorage (never localStorage)
7. Subsequent API calls include Bearer token

**Roles**: viewer, operator, admin
- All data endpoints require authentication
- Role checks on sensitive operations
- Audit logging for mutations

### Data Layer

**SQLite** (development): `sqlite+aiosqlite:///./data/vector_foundry.db`
**PostgreSQL** (production): `postgresql+asyncpg://user:pass@host/db`

**Tables**:
- `tracking_issues` — GitHub tracking issues with full metadata
- `checklist_items` — Parsed checklist items with completion status
- `issue_analyses` — Computed analysis results (readiness score, blockers, questions)
- `sync_logs` — GitHub sync operation history
- `users` — Synced Keycloak users with roles
- `audit_logs` — Mutation audit trail

### External Integrations

**GitHub API**: Fetches tracking issues from `rust-lang/rust` with label `tracking-issue`
- Rate limited without token (60/hr), higher with PAT (5000/hr)
- Syncs issue metadata, body, labels, comments
- Parses checklist, linked issues, unresolved questions

**Keycloak**: OIDC provider with SAML broker support
- Realm: `vector-foundry`
- Client: `vector-foundry-frontend` (public) + `vector-foundry-api` (confidential)
- Roles mapped from realm_access.claims

**LLM Providers** (optional):
- OpenAI-compatible (OpenAI, LiteLLM, OpenRouter, Ollama via /v1)
- Anthropic Messages API
- Google Gemini generateContent
- Ollama local (/api/generate)

## Data Flow

```
GitHub API → GitHubSyncService → SQLite (tracking_issues, checklist_items)
                                    ↓
                            AnalysisEngine → SQLite (issue_analyses)
                                    ↓
                         Issues API → Frontend (Dashboard/Detail/Compare)
                                    ↓
                            LLM API (opt-in) → LLM Provider → Frontend
```

## Deployment

### Development
```bash
docker compose up -d
# Frontend: http://localhost
# Backend:  http://localhost:8000
# Keycloak: http://localhost:8080
```

### Production
- Use PostgreSQL instead of SQLite
- Configure TLS reverse proxy (nginx/Traefik/Caddy)
- Set `ENVIRONMENT=production`, strong `SECRET_KEY`
- Disable `DEMO_MODE`
- Use managed Keycloak or run with production config
- Enable backup/restore for database

## Security Considerations

- All secrets via environment variables (`.env` not committed)
- No credentials in code, tests, or Docker images
- OIDC tokens validated with JWKS, issuer, audience checks
- Session tokens in memory (sessionStorage), not persisted
- CORS restricted to configured origins
- Rate limiting recommended at reverse proxy
- Regular dependency updates via Dependabot