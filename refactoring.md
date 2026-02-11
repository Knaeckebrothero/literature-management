# Refactoring Plan: General-Purpose SLR Tool

## Goal

Transform this project from a hardcoded "Virtual Tutors in Higher Education" SLR tool into a general-purpose Systematic Literature Review application that supports multiple projects with arbitrary topics.

## Core Concept

The current 8-phase LLM pipeline with hardcoded Pydantic models, enums, and prompts gets replaced by a simple agent-based approach:

```
agent = reasoning model + citation tool + context management

for each source, question:
    agent + source + question → structured answer
    content matrix += structured answer
```

The content matrix (sources × questions → answers) is the primary output. This is the artifact that typically represents ~80% of the work in a systematic literature review.

## User Assumptions

Target users are masters/PhD-level researchers who are technically proficient. No need for casual-user fallbacks. Users can provide configuration as JSON templates or Pydantic classes to define their project instructions and question structure.

## Architecture Changes

### 1. Add Project Table

Add a `projects` table so the app can manage multiple SLR projects:

- Each project has a topic, description, and configuration
- Sources are linked to projects via `project_sources` junction table (same source can appear in multiple projects)
- Content matrix config (questions, answer types) is stored per project in the `config` JSON field
- Dashboard gets a project selector dropdown

### 2. Strip Domain-Specific Hardcoding

Remove all virtual tutor / neurosymbolic AI references:

- Delete `src/assessment/` (8-phase pipeline, hardcoded Pydantic models, phase processors)
- Remove `virtual_tutor_assessments` table and all associated junction tables, views, indexes
- Clean hardcoded strings, metrics, and filters from the dashboard
- Remove domain-specific SQL queries from `src/main.py`

### 3. Content Matrix

Replace the fixed assessment schema with a flexible content matrix:

- User provides a config (JSON) defining the questions for their SLR
- Each cell in the matrix is: `(project, source, question) → structured answer`
- Answer structure defined per question: boolean, enum, text, numeric
- Store results in generic `content_matrix` table rather than 26 hardcoded columns

### 4. Agent-Based Assessment

Replace the 8-phase chain with a single agent loop:

- Agent processes one source + one question at a time
- Agent has access to: reasoning model, citation engine tool, source content
- No hardcoded prompts or conditional phase skipping
- Agent spends exactly the time needed per question (simple questions get simple answers, complex ones get deeper reasoning)

### 5. Keep What Works

- **Import pipeline** (`src/import_citations.py`) — BibTeX, CSV, PDF, arXiv import stays. Write target changes from `papers` to `sources` table. Flow becomes: parse file → upsert into global `sources` (dedup on DOI/hash) → link to current project via `project_sources`. Parsers themselves stay mostly the same.
- **Citation Engine** (`citation_engine/`) — already a separate package, becomes a tool for the agent
- **PDF extraction** (`src/process_papers.py`) — keep the extraction parts, remove assessment orchestration
- **Dashboard shell** (`src/main.py`) — keep the Streamlit structure, adapt to show content matrix and project-scoped data
- **Keywords / metadata** — keep existing keyword extraction and analysis, scope to projects via source junction
- **Database utilities** — connection helpers, setup functions stay

## Implementation Roadmap

### Phase 1: Clean Slate

**Goal:** Remove all domain-specific code, leaving a minimal working shell.

| Step | File(s) | Action |
|------|---------|--------|
| 1.1 | `src/assessment/` | Delete entire directory (8 phase processors, models.py, orchestrator) |
| 1.2 | `src/process_papers.py` | Remove `VirtualTutorAssessment` import and assessment logic; keep PDF extraction |
| 1.3 | `src/schema.sql` | Remove `virtual_tutor_assessments` table, all junction tables, views, indexes |
| 1.4 | `src/main.py` | Gut domain-specific tabs, queries, visualizations; keep Streamlit shell |
| 1.5 | `src/view_paper.py` | Remove assessment display logic if present |
| 1.6 | All `src/*.py` | Remove orphaned imports, dead code, "virtual tutor" strings |
| 1.7 | `CLAUDE.md` | Remove references to 8-phase pipeline, virtual tutors |

**Exit criteria:** App runs without errors, shows empty/placeholder UI.

---

### Phase 2: New Schema & Project Support

**Goal:** Implement the new data model and basic project selection.

| Step | File(s) | Action |
|------|---------|--------|
| 2.1 | `src/schema.sql` | Write new schema: `sources`, `projects`, `project_sources`, `content_matrix`, adapted `keywords` |
| 2.2 | `src/db.py` (or equivalent) | Update connection helpers if needed for new schema |
| 2.3 | `src/import_citations.py` | Change write target from `papers` to `sources`; add `project_sources` linking |
| 2.4 | `src/main.py` | Add project selector dropdown in sidebar; store selection in session state |
| 2.5 | `src/main.py` | Add Projects tab: create project form (name, topic, description) |
| 2.6 | `src/main.py` | Add Sources tab: show sources for selected project, import UI |
| 2.7 | All queries | Scope to `project_id` via `project_sources` junction |

**Exit criteria:** Can create projects, import sources into a project, view sources per project.

---

### Phase 3: Content Matrix

**Goal:** Implement question config, agent assessment, and matrix display.

| Step | File(s) | Action |
|------|---------|--------|
| 3.1 | `src/models.py` (new) | Pydantic models for `ProjectConfig`, `Question`, `Answer` |
| 3.2 | `src/main.py` | Projects tab: add config editor (JSON textarea or form) |
| 3.3 | `src/agent.py` (new) | Implement agent: reasoning model + citation tool + source context |
| 3.4 | `src/assessment.py` (new) | Assessment loop: for each (source, question) → call agent → store result |
| 3.5 | `src/main.py` | Content Matrix tab: display as table (sources × questions) |
| 3.6 | `src/main.py` | Content Matrix tab: "Run Assessment" button, progress indicator |
| 3.7 | `src/main.py` | Content Matrix tab: export to CSV/Excel |

**Exit criteria:** Can define questions, run assessment on sources, view and export matrix.

---

### Phase 4: Polish

**Goal:** Restore useful visualizations, improve UX, update docs.

| Step | File(s) | Action |
|------|---------|--------|
| 4.1 | `src/main.py` | Analysis tab: adapt keyword analysis to work from `sources` |
| 4.2 | `src/main.py` | Analysis tab: add matrix-based visualizations (answer distributions, etc.) |
| 4.3 | `src/main.py` | Projects tab: edit/delete project, duplicate project |
| 4.4 | `src/main.py` | Sources tab: bulk operations, source detail view |
| 4.5 | `CLAUDE.md` | Update with new architecture, commands, schema |
| 4.6 | `README.md` | Update if exists |

**Exit criteria:** Full-featured generic SLR tool ready for use.

## Data Model

Aligns with the citation engine's approach: **sources are global, citations/usage is project-scoped**.

- Sources (papers, web pages, etc.) live in a global `sources` table
- Uniquely identified by DOI when available, otherwise by document content hash
- Projects link to sources via a junction table
- Content matrix entries are project-scoped

### Schema Direction

```sql
-- Global source registry (aligned with citation engine)
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier TEXT NOT NULL UNIQUE,  -- DOI or content hash
    identifier_type TEXT NOT NULL,    -- 'doi' or 'hash'
    title TEXT,
    authors TEXT,
    year INTEGER,
    abstract TEXT,
    publication TEXT,
    source_type TEXT,                 -- 'journal', 'conference', 'preprint', 'web', etc.
    metadata TEXT,                    -- JSON: additional fields
    content TEXT,                     -- extracted full text (from PDF, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SLR projects
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    topic TEXT,
    description TEXT,
    config TEXT,  -- JSON: questions, answer types, agent settings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project ↔ Source junction (a source can appear in multiple projects)
CREATE TABLE project_sources (
    project_id INTEGER NOT NULL REFERENCES projects(id),
    source_id INTEGER NOT NULL REFERENCES sources(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, source_id)
);

-- Content matrix (project-scoped)
CREATE TABLE content_matrix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    source_id INTEGER NOT NULL REFERENCES sources(id),
    question_key TEXT NOT NULL,
    answer TEXT,
    answer_type TEXT,  -- 'boolean', 'enum', 'text', 'numeric'
    confidence REAL,
    citations TEXT,    -- JSON array of citation references
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, source_id, question_key)
);

-- Removed: papers table (replaced by sources), virtual_tutor_assessments, all junction tables
```

### Existing Data

No migration needed. The previous SLR project is completed; we start with a fresh schema.

### Keywords / Metadata

Keep the existing keyword extraction and metadata analysis functionality. It works generically and is useful across any SLR topic. Will be scoped to projects via the source junction.

## Project Configuration

The `config` JSON field in the projects table defines the questions and answer types for the content matrix.

### Config Structure

```json
{
  "questions": [
    {
      "key": "uses_llm",
      "text": "Does the system use a large language model?",
      "answer_type": "boolean"
    },
    {
      "key": "architecture",
      "text": "Describe the system architecture.",
      "answer_type": "text"
    },
    {
      "key": "evaluation_method",
      "text": "What evaluation methodology was used?",
      "answer_type": "enum",
      "options": ["controlled_experiment", "survey", "case_study", "none"]
    },
    {
      "key": "sample_size",
      "text": "What was the sample size of the evaluation?",
      "answer_type": "numeric"
    }
  ]
}
```

### Answer Types

- `boolean` — yes/no questions
- `text` — free-form text answers
- `enum` — select from predefined options (requires `options` array)
- `numeric` — numerical values

## Dashboard Structure

Reorganized for a generic SLR tool:

| Tab | Purpose |
|-----|---------|
| **Projects** | Create, select, configure projects. Project selector dropdown persists across tabs. |
| **Sources** | Import sources (BibTeX, CSV, PDF, arXiv). View/filter sources in current project. Manage source metadata. |
| **Content Matrix** | View matrix (sources × questions). Run agent assessment. Export to CSV/Excel. |
| **Analysis** | Keyword analysis, metadata visualizations, summary statistics. Scoped to current project. |

## Open Questions

- Exact agent implementation details (deferred until phase 3)
- Whether to support cross-source queries or keep it strictly single-source-per-question for now (start with single-source)
