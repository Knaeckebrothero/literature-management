# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Systematic Literature Review (SLR) tool for research on "Virtual Tutors in Higher Education". The system imports research papers from multiple sources, automatically assesses them through an 8-phase LLM-driven pipeline, and provides a Streamlit dashboard for visualization and analysis.

**Virtual Tutor Definition:** AI-based educational systems using NLP/LLMs in higher education for tutoring or learning support.

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
podman-compose up -d        # Start PostgreSQL
podman-compose down          # Stop PostgreSQL
```

## Architecture

### Main Components

1. **Streamlit Dashboard** (`src/main.py`) — Web UI with tabs: Papers, Assessments, Keywords, Analysis, Assessment Matrix

2. **Assessment Framework** (`src/assessment/`) — 8-phase LLM evaluation pipeline:
   - Phase 1: Initial filtering (is it a virtual tutor?)
   - Phase 2: Core system characteristics (LLM model, RAG, function)
   - Phase 3: Publication metadata
   - Phase 4: Technical architecture (skipped for theory papers)
   - Phase 5: Pedagogical features
   - Phase 6: Evaluation methodology
   - Phase 7: Implementation context (skipped for theory papers)
   - Phase 8: Privacy and compliance

   Each phase has a processor in `src/assessment/phases/phase{N}_{name}.py`. Phases 4 and 7 conditionally skip for theoretical (non-implementation) papers.

3. **Citation Engine** (`citation_engine/`) — Reusable package for LLM-based citation verification. Supports SQLite (single agent) and PostgreSQL (multi-agent) modes. Has LangChain/LangGraph tool wrappers in `citation_engine/src/citation_engine/tool.py`.

### Data Flow

```
Input Sources (BibTeX, CSV, PDF, arXiv)
    → CitationProcessor / PdfProcessor
    → SQLite Database (papers, virtual_tutor_assessments, keywords)
    → VirtualTutorAssessment (8-phase LLM pipeline)
    → Streamlit Dashboard (visualization, filtering, export)
```

### Key Files

- `src/main.py` — Main dashboard application
- `src/schema.sql` — Database schema with normalized junction tables for multi-valued fields
- `src/process_papers.py` — PDF extraction and LLM assessment with rate limiting
- `src/import_citations.py` — Citation import from BibTeX, IEEE CSV, Springer, DBLP, ProQuest formats
- `src/assessment/models.py` — Pydantic models for all 8 assessment phases
- `src/assessment/virtual_tutor_assessment.py` — Assessment orchestrator

### Database Design

Multi-valued assessment fields (architecture_components, interaction_modalities, pedagogical_features, etc.) are normalized into separate junction tables. Views include `papers_with_assessment_status`, `implementation_papers`, and `keyword_frequency`. Duplicate detection uses DOI and title+authors matching.

## Environment Variables

```bash
OPENAI_API_KEY=         # Required for LLM assessment
CITATION_DB_URL=        # PostgreSQL URL for Citation Engine multi-agent mode
CITATION_LLM_MODEL=     # Default: gpt-4o-mini
```

## Development Notes

- Python >= 3.10 required (project uses 3.12 venv)
- Uses Pydantic for structured LLM output validation
- Rate limiting implemented for API calls in `PdfProcessor`
- Citation Engine uses optional dependency extras (`full`, `pdf`, `web`, `langchain`, `postgresql`, `dev`)
- Database schema auto-applied on first connection via `setup_database_with_connection`
