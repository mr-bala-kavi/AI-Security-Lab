# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **Two new vulnerability modules**, completing broader OWASP LLM Top 10 coverage:
  - **Vector & Embedding Weaknesses (LLM08)** — a RAG pipeline with an injectable
    knowledge base. Learners poison the vector store and hijack retrieval to
    exfiltrate a confidential record. Uses a dependency-free TF cosine retriever
    so it runs fully offline.
  - **Misinformation & Overreliance (LLM09)** — an over-confident assistant that
    fabricates facts and invents authoritative-looking citations under pressure.
- **Threat Reference page** (`/reference`) mapping every module to the OWASP LLM
  Top 10 (2025) and MITRE ATLAS techniques.
- **Solution walkthroughs** (`/solutions`, `/solutions/<module>`) with worked
  exploits per security level and the corresponding fix.
- **Gamification**: an achievements system with badges, points and ranks
  (`/achievements`, `/api/achievements`).
- **Attack analytics dashboard** (`/analytics`, `/api/analytics`) with Chart.js
  visualisations of attempts, success rates, DoS metrics and tool calls.
- **Session export** (`/api/export`) — download progress, achievements,
  analytics and chat history as JSON.
- **Real rate limiting** (`utils/rate_limiter.py`): the previously unused
  `RATE_LIMIT_*` config is now enforced, and the HIGH security level is throttled
  as documented (returns HTTP 429).
- **Test suite** (`tests/`, 68 tests) covering the app, models, routes, helpers,
  rate limiter and achievements — runnable without the heavy ML stack.
- **CI** via GitHub Actions (lint + tests on Python 3.9/3.11/3.12 + Docker build).
- **Docker** support: `Dockerfile`, `docker-compose.yml`, `.dockerignore`.
- `CONTRIBUTING.md`, `requirements-dev.txt`, and this changelog.

### Fixed
- `_record_successful_exploit` now marks a module **completed** on the *first*
  successful exploit. Previously `completed` was only set in the `ON CONFLICT`
  update branch, so a module solved once was never marked complete.
- The database `close_db` teardown is now registered (`init_db.init_app` was
  defined but never called), so connections are released at the end of each
  request.
- Reset now also clears injected RAG documents and the session's rate-limit
  buckets.

### Changed
- Dashboard module/hint counts are now derived from the module registry instead
  of being hard-coded (8 → 10 modules).
- Added global navigation links (Analytics, Achievements, Reference, Solutions).

## [1.0.0] - Initial release
- 8 AI/ML vulnerability modules, 3 security levels, hint system, progress
  tracking, dark mode, SQLite persistence, and PyTorch/Transformers models with
  rule-based fallbacks.
