-- Literature Management System Database Schema
-- General-purpose Systematic Literature Review tool

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Global source registry (papers, web pages, etc.)
-- Uniquely identified by DOI when available, otherwise by content hash
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier TEXT NOT NULL UNIQUE,  -- DOI or content hash
    identifier_type TEXT NOT NULL,    -- 'doi' or 'hash'
    title TEXT,
    authors TEXT,
    year INTEGER,
    abstract TEXT,
    publication TEXT,                 -- journal/conference name
    source_type TEXT,                 -- 'journal', 'conference', 'preprint', 'web', etc.
    import_source TEXT,               -- where imported from: 'ieee', 'springer', 'bibtex', 'manual'
    metadata TEXT,                    -- JSON: additional fields
    content TEXT,                     -- extracted full text (from PDF, etc.)
    file_path TEXT,                   -- path to local PDF if available
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SLR projects
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    topic TEXT,
    description TEXT,
    config TEXT,  -- JSON: questions, answer types, agent settings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project <-> Source junction (a source can appear in multiple projects)
CREATE TABLE IF NOT EXISTS project_sources (
    project_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, source_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

-- Content matrix (project-scoped assessment results)
CREATE TABLE IF NOT EXISTS content_matrix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    question_key TEXT NOT NULL,
    answer TEXT,
    answer_type TEXT,  -- 'boolean', 'enum', 'text', 'numeric'
    confidence REAL,
    citations TEXT,    -- JSON array of citation references
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, source_id, question_key),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

-- Keywords table
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT UNIQUE
);

-- Relationship table for keywords and sources (many-to-many)
CREATE TABLE IF NOT EXISTS rel_keywords_sources (
    source_id INTEGER,
    keyword_id INTEGER,
    PRIMARY KEY (source_id, keyword_id),
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
);

-- Indexes for better query performance

-- Sources indexes
CREATE INDEX IF NOT EXISTS idx_sources_identifier ON sources(identifier);
CREATE INDEX IF NOT EXISTS idx_sources_year ON sources(year);
CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_import ON sources(import_source);

-- Projects indexes
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);

-- Project sources indexes
CREATE INDEX IF NOT EXISTS idx_ps_project ON project_sources(project_id);
CREATE INDEX IF NOT EXISTS idx_ps_source ON project_sources(source_id);

-- Content matrix indexes
CREATE INDEX IF NOT EXISTS idx_cm_project ON content_matrix(project_id);
CREATE INDEX IF NOT EXISTS idx_cm_source ON content_matrix(source_id);
CREATE INDEX IF NOT EXISTS idx_cm_question ON content_matrix(question_key);

-- Keywords indexes
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_rel_ks_source ON rel_keywords_sources(source_id);
CREATE INDEX IF NOT EXISTS idx_rel_ks_keyword ON rel_keywords_sources(keyword_id);

-- Views for common queries

-- View for keyword frequency analysis (global)
CREATE VIEW IF NOT EXISTS keyword_frequency AS
SELECT
    k.keyword,
    COUNT(r.source_id) as source_count
FROM keywords k
    LEFT JOIN rel_keywords_sources r ON k.id = r.keyword_id
GROUP BY k.id, k.keyword
ORDER BY source_count DESC;

-- View for project sources with details
CREATE VIEW IF NOT EXISTS project_sources_view AS
SELECT
    ps.project_id,
    p.name as project_name,
    s.id as source_id,
    s.identifier,
    s.title,
    s.authors,
    s.year,
    s.publication,
    s.source_type,
    s.import_source,
    ps.added_at
FROM project_sources ps
    JOIN projects p ON ps.project_id = p.id
    JOIN sources s ON ps.source_id = s.id;
