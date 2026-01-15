# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Systematic Literature Review (SLR) tool for research on "Virtual Tutors in Higher Education". The system imports research papers from multiple sources, automatically assesses them through an 8-phase LLM-driven pipeline, and provides a Streamlit dashboard for visualization and analysis.

**Virtual Tutor Definition:** AI-based educational systems using NLP/LLMs in higher education for tutoring or learning support.

## Common Commands

```bash
# Run the main dashboard
streamlit run src/main.py

# Run Citation Engine tests
cd CitationEngine
pytest tests/test_engine.py -v                    # Unit tests
pytest tests/ -v --cov=src/citation_engine        # With coverage

# Integration tests (require environment setup)
RUN_POSTGRES_TESTS=true pytest tests/test_integration_postgres.py -v
RUN_LLM_TESTS=true pytest tests/test_integration_llm.py -v -s
RUN_WEB_TESTS=true pytest tests/test_integration_web.py -v -s

# Code quality (Citation Engine)
ruff check src/
ruff format src/
mypy src/

# Install dependencies
pip install -r requirements.txt

# Install Citation Engine with all features
cd CitationEngine && pip install -e ".[full,dev]"
```

## Architecture

### Main Components

1. **Streamlit Dashboard** (`src/main.py`) - Web UI with tabs: Papers, Assessments, Keywords, Analysis, Assessment Matrix

2. **Assessment Framework** (`src/assessment/`) - 8-phase LLM evaluation pipeline:
   - Phase 1: Initial filtering (is it a virtual tutor?)
   - Phase 2: Core system characteristics (LLM model, RAG, function)
   - Phase 3: Publication metadata
   - Phase 4: Technical architecture (skipped for theory papers)
   - Phase 5: Pedagogical features
   - Phase 6: Evaluation methodology
   - Phase 7: Implementation context (skipped for theory papers)
   - Phase 8: Privacy and compliance

3. **Citation Engine** (`CitationEngine/`) - Reusable package for LLM-based citation verification with SQLite/PostgreSQL support

### Data Flow

```
Input Sources (BibTeX, CSV, PDF, arXiv)
    → CitationProcessor / PdfProcessor
    → SQLite Database (papers, virtual_tutor_assessments, keywords)
    → VirtualTutorAssessment (8-phase LLM pipeline)
    → Streamlit Dashboard (visualization, filtering, export)
```

### Key Files

- `src/main.py` - Main dashboard application
- `src/schema.sql` - Database schema with normalized tables for multi-valued fields
- `src/process_papers.py` - PDF extraction and LLM assessment with rate limiting
- `src/import_citations.py` - Citation import from BibTeX and various CSV formats
- `src/assessment/models.py` - Pydantic models for 8 assessment phases
- `src/assessment/virtual_tutor_assessment.py` - Assessment orchestrator

### Database Design

Multi-valued assessment fields (architecture_components, interaction_modalities, pedagogical_features, etc.) are normalized into separate junction tables rather than stored as delimited strings.

## Environment Variables

```bash
OPENAI_API_KEY=         # Required for LLM assessment
CITATION_DB_URL=        # PostgreSQL URL for Citation Engine multi-agent mode
CITATION_LLM_MODEL=     # Default: gpt-4o-mini
```

## Development Notes

- Uses Pydantic for structured LLM output validation
- Rate limiting implemented for API calls in `PdfProcessor`
- Phases 4 and 7 conditionally skip for theoretical (non-implementation) papers
- Citation Engine supports both SQLite (single agent) and PostgreSQL (multi-agent) modes
