# Literature Management System

> A general-purpose Systematic Literature Review (SLR) tool with LLM-powered content matrix assessment.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey)

## Key Features

- **Multi-Project Support** - Manage multiple SLR projects with independent configurations
- **Configurable Content Matrix** - Define custom questions with boolean, enum, text, or numeric answer types
- **LLM-Powered Assessment** - Automated source analysis using OpenAI-compatible models
- **Multi-Source Import** - Support for BibTeX, IEEE CSV, and Springer CSV formats
- **Interactive Dashboard** - Streamlit-based UI with visualizations and filtering
- **Export Capabilities** - Export content matrix to CSV or JSON with full metadata

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [Configuration Format](#configuration-format)
- [Environment Variables](#environment-variables)

## Installation

### Prerequisites

- Python 3.10 or higher
- Git
- OpenAI API key (or compatible endpoint)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/Knaeckebrothero/literature-management.git
cd literature-management
```

2. **Create a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=your_key_here
```

## Quick Start

### Running the Application

```bash
streamlit run src/main.py
```

The application opens at `http://localhost:8501`

### Basic Workflow

1. **Create a Project** - Go to Projects tab, enter name and topic
2. **Configure Questions** - Add JSON config defining your content matrix questions
3. **Import Sources** - Place citation files in `search_results/` and click Import
4. **Run Assessment** - Go to Content Matrix tab and click "Run Assessment"
5. **Review & Export** - View results, filter, and export to CSV/JSON

## Project Structure

```
literature-management/
├── src/
│   ├── main.py              # Main Streamlit dashboard
│   ├── models.py            # Pydantic models for config and answers
│   ├── agent.py             # LLM assessment agent
│   ├── assessment.py        # Assessment orchestration loop
│   ├── import_citations.py  # Citation import handlers
│   ├── schema.sql           # Database schema
│   └── process_papers.py    # PDF extraction utilities
├── citation_engine/         # Reusable citation verification package
├── search_results/          # Place citation files here (BibTeX, CSV)
├── papers/                  # PDF storage directory
├── literature.db            # SQLite database (auto-created)
├── requirements.txt
├── .env.example
└── CLAUDE.md               # Development documentation
```

## Usage Guide

### Projects Tab

Create and manage SLR projects. Each project has:
- **Name** and **Topic** - Project identification
- **Description** - Detailed project notes
- **Config** - JSON configuration for content matrix questions

Actions: Select, Edit, Duplicate, Delete projects.

### Sources Tab

View and manage sources for the selected project (or all sources globally).

Features:
- Search and filter sources
- View full source details (abstract, keywords, content)
- Bulk operations: add to project, remove from project, delete
- Export to CSV
- Publications by year chart

### Content Matrix Tab

The core SLR analysis tool. Displays a matrix of sources (rows) vs questions (columns).

Features:
- **Run Assessment** - LLM analyzes all sources against configured questions
- **Progress tracking** - See assessment progress in real-time
- **Visualizations** - Confidence distribution, answer distributions, completion heatmap
- **Export** - CSV (summary) or JSON (full details with citations)

### Keywords Tab

Analyze keyword frequency across sources. Scoped to the selected project or global.

### Add Source Tab

Manually add sources with title, authors, year, DOI, and other metadata.

## Configuration Format

Project configuration is stored as JSON. Define questions for your content matrix:

```json
{
  "questions": [
    {
      "key": "uses_llm",
      "text": "Does the system use a large language model?",
      "answer_type": "boolean",
      "description": "Look for mentions of GPT, BERT, LLaMA, or similar"
    },
    {
      "key": "evaluation_method",
      "text": "What evaluation methodology was used?",
      "answer_type": "enum",
      "options": ["controlled_experiment", "survey", "case_study", "none"]
    },
    {
      "key": "sample_size",
      "text": "What was the sample size?",
      "answer_type": "numeric"
    },
    {
      "key": "main_contribution",
      "text": "What is the main contribution?",
      "answer_type": "text"
    }
  ],
  "model": "gpt-4o-mini",
  "system_prompt": "Optional custom system prompt for the agent"
}
```

### Answer Types

| Type | Description | Example |
|------|-------------|---------|
| `boolean` | Yes/No questions | "Does it use RAG?" |
| `enum` | Select from options | "What methodology?" |
| `text` | Free-form text | "Main contribution?" |
| `numeric` | Numerical values | "Sample size?" |

## Environment Variables

```bash
# Required for LLM assessment
OPENAI_API_KEY=sk-...

# Optional: Custom model (default: gpt-4o-mini)
CITATION_LLM_MODEL=gpt-4o-mini

# Optional: OpenAI-compatible endpoint
CITATION_LLM_URL=https://api.example.com/v1
```

## Citation Engine

The `citation_engine/` directory contains a reusable package for LLM-based citation verification. See `citation_engine/README.md` for details.

## Development

See `CLAUDE.md` for development documentation, commands, and architecture details.

## License

MIT License - see LICENSE file for details.
