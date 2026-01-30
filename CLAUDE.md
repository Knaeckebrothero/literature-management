# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A general-purpose Systematic Literature Review (SLR) tool. The system imports research papers from multiple sources, supports configurable content matrix questions, and provides a Streamlit dashboard for management, LLM-powered assessment, and analysis.

## Branching Model

- `main` — stable branch, target for pull requests
- `develop` — active development branch
- Feature branches merge into `develop` via PR, then `develop` merges into `main`

## Common Commands

```bash
# Run the main dashboard
streamlit run src/main.py

# Install dependencies
pip install -r requirements.txt

# Install Citation Engine with all features (from repo root)
cd citation_engine && pip install -e ".[full,dev]"
```

### Citation Engine Tests

All test commands run from the `citation_engine/` directory:

```bash
# Unit tests
pytest tests/test_engine.py -v

# All tests with coverage
pytest tests/ -v --cov=src/citation_engine

# Run a single test
pytest tests/test_engine.py::TestClassName::test_method_name -v

# Integration tests (gated by environment variables)
RUN_POSTGRES_TESTS=true pytest tests/test_integration_postgres.py -v
RUN_LLM_TESTS=true pytest tests/test_integration_llm.py -v -s
RUN_WEB_TESTS=true pytest tests/test_integration_web.py -v -s
```

Pytest markers: `@pytest.mark.postgres`, `@pytest.mark.llm`, `@pytest.mark.web`, `@pytest.mark.integration`.

### Code Quality (Citation Engine)

Run from `citation_engine/` directory:

```bash
ruff check src/
ruff format src/ tests/
mypy src/
```

Ruff config: line-length 100, target Python 3.10, selects E/W/F/I/B/C4/UP rules (E501 ignored).

### PostgreSQL Dev Environment

```bash
cd citation_engine
podman-compose up -d                    # Start PostgreSQL
podman-compose --profile admin up -d    # Start PostgreSQL + pgAdmin (port 5050)
podman-compose down                     # Stop services
podman-compose down -v                  # Stop and remove volumes
```

## Architecture

### Main Components

1. **Streamlit Dashboard** (`src/main.py`) — Web UI with tabs: Projects, Sources, Content Matrix, Keywords, Add Source. Supports multiple SLR projects with project-scoped views.

2. **Content Matrix Assessment** — Agent-based assessment of sources against configured questions:
   - `src/models.py` — Pydantic models for ProjectConfig, Question, Answer types
   - `src/agent.py` — LLM-based assessment agent using OpenAI API
   - `src/assessment.py` — Assessment orchestration loop with progress tracking

3. **Citation Engine** (`citation_engine/`) — Reusable package for LLM-based citation verification. Supports SQLite (single agent) and PostgreSQL (multi-agent) modes. Has LangChain/LangGraph tool wrappers in `citation_engine/src/citation_engine/tool.py`.

4. **Import Pipeline** (`src/import_citations.py`) — Citation import from BibTeX, IEEE CSV, Springer formats. Imports to global sources table with optional project linking.

### Data Flow

```
Input Sources (BibTeX, CSV)
    → CitationProcessor (with optional project_id)
    → SQLite Database (sources, project_sources, keywords)
    → Streamlit Dashboard (project-scoped visualization, filtering, export)

Content Matrix Assessment:
    Project Config (questions)
    + Sources (abstract/content)
    → AssessmentAgent (LLM reasoning)
    → content_matrix table (source × question → answer)
    → Dashboard display + CSV/JSON export
```

### Key Files

- `src/main.py` — Main dashboard application with all tabs
- `src/models.py` — Pydantic models for project config and content matrix
- `src/agent.py` — Assessment agent for analyzing sources
- `src/assessment.py` — Assessment loop orchestration
- `src/schema.sql` — Database schema (sources, projects, project_sources, content_matrix, keywords)
- `src/import_citations.py` — Citation import from BibTeX, IEEE CSV, Springer formats
- `src/process_papers.py` — PDF metadata extraction utilities

### Database Design

The schema supports multiple SLR projects:

- **sources** — Global registry of papers/documents (identified by DOI or content hash)
- **projects** — SLR projects with name, topic, description, and JSON config for content matrix questions
- **project_sources** — Junction table linking sources to projects (many-to-many)
- **content_matrix** — Project-scoped assessment results (source × question → answer)
- **keywords** — Global keyword registry
- **rel_keywords_sources** — Keywords linked to sources

Views: `keyword_frequency`, `project_sources_view`

## Environment Variables

```bash
OPENAI_API_KEY=                    # Required for LLM features
CITATION_DB_URL=                   # PostgreSQL URL for Citation Engine multi-agent mode
CITATION_LLM_MODEL=               # Default: gpt-4o-mini
CITATION_LLM_URL=                  # OpenAI-compatible endpoint URL (optional)
CITATION_REASONING_REQUIRED=low    # none|low|medium|high — LLM reasoning depth for verification
```

## Development Notes

- Python >= 3.10 required (project uses 3.12 venv)
- Citation Engine uses optional dependency extras (`full`, `pdf`, `web`, `langchain`, `postgresql`, `dev`)
- Database schema auto-applied on first connection via `setup_database_with_connection`
- Dev container available (`.devcontainer/`) with Python 3.12, Tesseract OCR, and poppler-utils
- Main database file: `literature.db` (SQLite) at project root
