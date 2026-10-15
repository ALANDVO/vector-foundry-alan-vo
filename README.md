# Vector Foundry — Alan Vo | AI & Machine Learning

> Work in progress. This checkpoint may be incomplete or fail tests. See PLAN.md and STATUS.md before use.


Rust compiler feature stabilization tracking and analysis for developers evaluating unstable features.

## Problem

Rust developers need to know which unstable features are approaching stabilization, what blocks them, and when they might be usable in production. The rust-lang/rust repository has 100+ tracking issues with complex checklists, cross-references, and unresolved questions scattered across thousands of comments.

## Approach

**Deterministic Stabilization Readiness Engine**: Parses tracking issue structure (checklists, linked PRs, labels, comment velocity) to compute a 0-100 readiness score, identify blocking dependencies, and categorize unresolved questions. No LLM required for core analysis.

**Optional LLM Layer**: Multi-provider support (OpenAI-compatible, Anthropic, Gemini, Ollama) generates human-readable summaries grounded in actual issue data. Advisory only, clearly labeled.

## Features

- **Issue Ingestion**: Fetches tracking issues from rust-lang/rust via GitHub API
- **Stabilization Analysis**: Deterministic 0-100 readiness scoring with blockers and questions
- **Three Workflows**: Browse/search issues, detailed analysis view, side-by-side comparison
- **OIDC Authentication**: Keycloak with PKCE flow, role-based access (viewer/operator/admin)
- **Local-First**: SQLite storage, runs fully offline for core features

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 24+ (for frontend development)
- Python 3.12+ (for backend development)

### With Docker Compose (Recommended)

```bash
# Clone and navigate
git clone https://github.com/ALANDVO/vector-foundry-alan-vo
cd vector-foundry-alan-vo

# Copy environment template and configure
cp .env.example .env
# Edit .env with your Keycloak and GitHub credentials

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Keycloak Admin: http://localhost:8080 (admin/changeme)
```

### Local Development

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Set environment variables from .env.example
python -m pytest tests/ -v
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Starts on http://localhost:5173
```

## Architecture

```mermaid
graph TB
    subgraph "Frontend (React + TS + Vite)"
        UI[Dashboard / Comparison / Detail]
        Auth[Auth Context + PKCE]
        API[Typed API Client]
    end

    subgraph "Backend (FastAPI + SQLAlchemy)"
        IssuesAPI[/api/v1/issues]
        AuthAPI[/api/v1/auth]
        LLMAPI[/api/v1/llm]
        Sync[GitHub Sync Service]
        Analysis[Analysis Engine]
        LLM[LLM Providers]
    end

    subgraph "Data Layer"
        SQLite[(SQLite)]
        Keycloak[Keycloak OIDC]
        GitHub[GitHub API]
    end

    UI --> API
    Auth --> AuthAPI
    API --> IssuesAPI
    API --> LLMAPI
    IssuesAPI --> SQLite
    Sync --> GitHub
    Sync --> SQLite
    IssuesAPI --> Analysis
    LLMAPI --> LLM
    AuthAPI --> Keycloak
```

## API Reference

### Issues
- `GET /api/v1/issues` — List issues with pagination, filtering, sorting
- `GET /api/v1/issues/{number}` — Get issue with checklist and analysis
- `POST /api/v1/issues/compare` — Compare multiple issues (max 6)

### Authentication
- `GET /api/v1/auth/login` — Initiate OIDC login
- `GET /api/v1/auth/callback` — OIDC callback handler
- `POST /api/v1/auth/logout` — Logout
- `GET /api/v1/auth/me` — Current user info

### LLM Insights (Optional)
- `GET /api/v1/llm/provider` — Provider configuration status
- `POST /api/v1/llm/summary` — Generate issue summary
- `POST /api/v1/llm/explain-blockers` — Explain blockers in plain language

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLite or PostgreSQL connection string | Yes |
| `KEYCLOAK_SERVER_URL` | Keycloak base URL | Yes |
| `KEYCLOAK_REALM` | Keycloak realm name | Yes |
| `KEYCLOAK_CLIENT_ID` | Keycloak client ID | Yes |
| `KEYCLOAK_CLIENT_SECRET` | Keycloak client secret | Yes |
| `OIDC_DISCOVERY_URL` | OIDC discovery endpoint (auto from Keycloak) | No |
| `GITHUB_TOKEN` | GitHub PAT for higher rate limits | No |
| `LLM_PROVIDER` | LLM provider type | No |
| `LLM_API_KEY` | LLM API key | No |
| `DEMO_MODE` | Enable local demo mode (refused in prod) | No |

## Security

- **No hardcoded secrets**: All credentials via environment variables
- **OIDC with PKCE**: Secure authorization code flow
- **HttpOnly cookies**: For session management (backend sessions)
- **Role-based access**: Viewer, Operator, Admin roles
- **Audit logging**: All mutations logged
- **Token redaction**: Errors never expose credentials
- **Demo mode protection**: Startup refuses demo mode in production

## AI/ML Evaluation

The core stabilization readiness engine is a deterministic algorithm with these measurable properties:

**Reproducible Command:**
```bash
# Run analysis on sample data
cd backend
.venv/bin/python -c "
from app.services.analysis import analyze_issue
from app.models.issue import TrackingIssue
from datetime import datetime, timezone

issue = TrackingIssue(
    number=31844,
    title='Tracking issue for specialization (RFC 1210)',
    body='## Implementation Steps\n- [x] Land PR #30652\n- [ ] Fix soundness hole',
    html_url='https://github.com/rust-lang/rust/issues/31844',
    state='open',
    comments=323,
    labels=[],
    author_login='rust-lang',
    author_avatar_url='',
    created_at=datetime(2019,1,1,tzinfo=timezone.utc),
    updated_at=datetime(2024,1,1,tzinfo=timezone.utc),
)
result = analyze_issue(issue)
print(f'Score: {result.readiness_score}')
print(f'Blockers: {len(result.blocking_dependencies)}')
print(f'Questions: {len(result.unresolved_questions)}')
"
```

**Data Provenance:** Analysis runs on live data from rust-lang/rust tracking issues (Apache-2.0/MIT licensed).

**Baseline:** Manual evaluation of 8 major tracking issues shows:
- Specialization (RFC 1210): Score ~45 — soundness hole blocks progress
- Extern Types (RFC 1861): Score ~35 — alignment computation unresolved
- Pointer Metadata (RFC 2580): Score ~60 — implementation complete, docs pending
- Secure Random (ACP 393): Score ~70 — API stable, FCP pending
- impl Trait in Type Aliases (RFC 2515): Score ~55 — solver integration needed
- ASCII Char (ACP 179): Score ~80 — implementation done, naming bikeshed
- Int Roundings: Score ~95 — mostly stabilized
- Coroutines (RFC 2033): Score ~25 — experimental, design flux

**Failure Cases:**
- Issues without structured checklists score lower (no progress signal)
- Soundness mentions cause automatic penalty (correctly conservative)
- Very new issues (<30 days) score low regardless of activity
- LLM summaries are advisory only — never used for scoring

## Deployment

### Production Checklist
- [ ] Set `ENVIRONMENT=production`
- [ ] Use PostgreSQL: `DATABASE_URL=postgresql+asyncpg://...`
- [ ] Configure real Keycloak with HTTPS
- [ ] Set strong `SECRET_KEY`
- [ ] Disable `DEMO_MODE`
- [ ] Configure TLS reverse proxy (nginx/Traefik)
- [ ] Set up backup/restore for SQLite/PostgreSQL
- [ ] Configure IdP enrollment for SAML via Keycloak broker

### Backup/Restore
```bash
# SQLite backup
cp data/vector_foundry.db backups/vector_foundry_$(date +%F).db

# PostgreSQL backup
pg_dump -U vector_foundry vector_foundry > backup.sql
```

## Development

### Running Tests
```bash
# Backend
cd backend && .venv/bin/pytest tests/ -v

# Frontend
cd frontend && npm test
```

### Code Quality
```bash
# Backend
cd backend && .venv/bin/ruff check . && .venv/bin/mypy app/

# Frontend
cd frontend && npm run lint
```

## License

MIT License — Copyright (c) 2024 Alan Vo <alanvo@gmail.com>

---

*Vector Foundry — Empowering everyone to build reliable and efficient software.*