# Literature Management System for Virtual Tutors Research

> A sophisticated systematic literature review system that leverages Large Language Models (LLMs) to automatically assess and categorize academic papers about virtual tutors in higher education through an 8-phase evaluation pipeline.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey)

## Key Features

- **Automated Assessment Pipeline** - 8-phase LLM-powered analysis for comprehensive paper evaluation
- **Multi-source Citation Import** - Support for BibTeX, CSV from IEEE, Springer, ACM databases
- **Interactive Dashboard** - Streamlit-based UI with real-time visualizations and filtering
- **Assessment Matrix** - Advanced filtering with heatmap visualization of paper characteristics
- **Export Capabilities** - Generate Excel/CSV reports with complete metadata and assessments
- **Smart Paper Processing** - Automatic text extraction from PDFs with DOI standardization

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [Assessment Phases](#assessment-phases)
- [Database Schema](#database-schema)
- [API Configuration](#api-configuration)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8 or higher
- Git
- OpenAI API key (or Replicate API token as alternative)

### Step-by-Step Setup

1. **Clone the repository**
```bash
git clone https://github.com/Knaeckebrothero/literature-management.git
cd literature-management
```

2. **Create a virtual environment**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=your_openai_api_key_here
# REPLICATE_API_TOKEN=your_replicate_token_here (optional)
```

5. **Initialize the database** (automatic on first run)
```bash
# The database will be created automatically when you first run the application
# Or you can manually initialize it:
python -c "from src.main import init_db; init_db()"
```

## Quick Start

### Running the Application

```bash
# Activate your virtual environment first
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux

# Launch the main application
streamlit run src/main.py
```

The application will open in your browser at `http://localhost:8501`

### Processing Your First Papers

1. **Import Citations**
   - Place your BibTeX files in `search_results/` directory
   - Or import CSV files from IEEE, Springer, ACM

2. **Add PDF Papers**
   - Place PDFs in the `papers/` directory
   - The system will automatically extract text and metadata

3. **Run Assessment**
   - Navigate to the Papers tab in the UI
   - Select papers to assess
   - Click "Run Assessment" to start the 8-phase analysis

4. **View Results**
   - Assessment Matrix tab: View all assessed papers with filtering
   - Analysis Dashboard: Explore visualizations and statistics
   - Export results to Excel/CSV for further analysis

## Project Structure

```
literature-management/
├── src/                           # Source code
│   ├── main.py                   # Main Streamlit application
│   ├── process_papers.py         # PDF processing pipeline
│   ├── import_citations.py       # Citation import handling
│   ├── schema.sql                # Database schema definition
│   ├── assessment/               # Assessment system
│   │   ├── virtual_tutor_assessment.py  # Main orchestrator
│   │   ├── models.py             # Pydantic data models
│   │   ├── phase_processor.py    # Base processor class
│   │   └── phases/               # Phase-specific processors
│   │       ├── phase1_filtering.py      # Virtual tutor identification
│   │       ├── phase2_core.py           # Core characteristics
│   │       ├── phase3_metadata.py       # Publication metadata
│   │       ├── phase4_technical.py      # Technical architecture
│   │       ├── phase5_pedagogical.py    # Pedagogical features
│   │       ├── phase6_evaluation.py     # Empirical evaluation
│   │       ├── phase7_context.py        # Implementation context
│   │       └── phase8_additional.py     # Ethics & limitations
│   └── test_assessment.py        # Assessment system tests
├── papers/                        # PDF storage directory
├── arxiv_papers/                  # ArXiv papers collection
├── search_results/                # Citation data (BibTeX, CSV)
├── content_matrix/                # Analysis outputs
├── literature.db                  # SQLite database
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
└── CLAUDE.md                     # Development documentation
```

## Usage Guide

### Processing Papers

The system processes papers through multiple stages:

1. **Import** - Load citations from BibTeX or CSV files
2. **Extract** - Pull text content from PDF files
3. **Assess** - Run through 8-phase LLM analysis
4. **Review** - Examine results in the dashboard
5. **Export** - Generate reports for your research

### Using the Dashboard

#### Papers Tab
- Browse all imported papers
- Filter by year, venue, assessment status
- Select papers for batch assessment
- View individual paper details

#### Assessment Matrix Tab
- Advanced filtering interface
- Heatmap visualization of paper characteristics
- Export filtered results to Excel
- Quick statistics overview

#### Analysis Dashboard
- Publication trends over time
- Venue distribution analysis
- Feature correlation networks
- Implementation approach breakdown

### Exporting Data

```python
# Export options available in the UI:
- Excel format with multiple sheets
- CSV for data analysis tools
- Filtered subsets based on criteria
- Complete assessment details
```

## Assessment Phases

The system evaluates papers through 8 sequential phases:

### Phase 1: Filtering
- Identifies if paper describes a virtual tutor system
- Distinguishes from general AI education tools

### Phase 2: Core Characteristics
- LLM model identification (GPT-4, Claude, Llama, etc.)
- RAG (Retrieval-Augmented Generation) usage
- Primary function and subject domain

### Phase 3: Metadata
- Publication type (journal, conference, preprint)
- Public availability status

### Phase 4: Technical Architecture
- System integration details
- Interaction modalities (chat, voice, etc.)
- Analytics and monitoring features

### Phase 5: Pedagogical Features
- Personalization capabilities
- Collaboration support
- Teaching methodologies

### Phase 6: Evaluation
- Empirical evaluation methodology
- Sample size and study duration
- Measured outcomes

### Phase 7: Context
- Institution type and location
- Development approach
- Language support

### Phase 8: Additional
- Privacy and ethics considerations
- Cost and resource requirements
- Future work directions

## Database Schema

### Main Tables

```sql
-- Core paper information
papers (
    doi, title, authors, venue, year, 
    abstract, url, keywords, citations_count
)

-- Comprehensive assessment results
virtual_tutor_assessments (
    paper_doi, is_virtual_tutor, llm_model,
    uses_rag, primary_function, subject_domain,
    [30+ additional fields across 8 phases]
)

-- Processing status tracking
assessment_phases (
    paper_doi, phase_number, status,
    started_at, completed_at, error_message
)
```

### Key Relationships
- Papers ↔ Assessments (1:1)
- Papers ↔ Keywords (M:N)
- Assessments ↔ Features (1:N normalized tables)

## API Configuration

### OpenAI Setup

1. Get your API key from [OpenAI Platform](https://platform.openai.com)
2. Add to `.env` file:
```env
OPENAI_API_KEY=sk-...your-key-here...
```

### Replicate Alternative (Optional)

For using alternative LLMs via Replicate:
```env
REPLICATE_API_TOKEN=r8_...your-token-here...
```

### Rate Limiting

The system includes automatic rate limiting:
- Configurable delays between API calls
- Retry logic for transient failures
- Cost-aware processing options

## Troubleshooting

### Common Issues

#### Database Lock Errors
```bash
# Stop all Python processes and restart
# Or delete literature.db and reinitialize
```

#### PDF Extraction Failures
- Ensure PDFs are not password-protected
- Check for corrupt files
- Try alternative extraction with PyPDFLoader

#### API Rate Limits
- Adjust delay settings in `process_papers.py`
- Use batch processing for large datasets
- Consider Replicate API for higher limits

#### Memory Issues with Large PDFs
- Process papers in smaller batches
- Increase Python memory limit
- Use text extraction preprocessing

### Debug Mode

Enable detailed logging:
```python
# In your .env file
DEBUG=True
LOG_LEVEL=DEBUG
```