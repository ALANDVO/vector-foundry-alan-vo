# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to Vector Foundry will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-15

### Added
- **Project skeleton**: FastAPI backend with React + TypeScript + Vite frontend
- **Docker Compose stack**: Backend, frontend, Keycloak, PostgreSQL with healthchecks
- **CI/CD pipeline**: GitHub Actions workflow for backend tests, frontend typecheck/build/test, Docker builds
- **OIDC Authentication**: Keycloak integration with PKCE flow, role-based access (viewer/operator/admin)
- **Rust Issue Tracker**: GitHub API ingestion for rust-lang/rust tracking issues with SQLite storage
- **Stabilization Analysis Engine**: Deterministic 0-100 readiness scoring with checklist parsing, blocker detection, unresolved question extraction
- **Three Workflows**:
  - Browse/Search: Filterable, sortable issue list with pagination
  - Detail View: Full issue with checklist, analysis, readiness score, blockers, questions
  - Comparison: Side-by-side metrics for up to 6 issues
- **LLM Insights (Optional)**: Multi-provider support (OpenAI-compatible, Anthropic, Gemini, Ollama) for advisory summaries
- **Documentation**: README with architecture diagram, API reference, deployment guide, AI/ML evaluation section
- **Portfolio metadata**: portfolio.json with schema_version, workflows, auth, llm_providers

### Security
- No hardcoded secrets; all credentials via environment variables
- HttpOnly SameSite cookies for session management
- CSRF protection on state-changing operations
- Token redaction in error responses
- Demo mode explicitly enabled, refused in production
- Audit logging for all mutations

### Testing
- 12+ backend tests covering health, issues API, analysis engine, GitHub sync, auth, LLM
- 3+ frontend tests covering app rendering, authentication context, navigation
- Integration tests for cross-service workflows

### Infrastructure
- Non-root Docker users for all services
- .dockerignore files for minimal build contexts
- SQLite for development, PostgreSQL-ready for production
- Keycloak realm import ready for SAML broker setup