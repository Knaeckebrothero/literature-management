-- Literature Management System Database Schema
-- For systematic literature review on virtual tutors in higher education

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Main table for research papers
CREATE TABLE IF NOT EXISTS papers (
                                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                                      doi TEXT UNIQUE,
                                      title TEXT,
                                      publication_year INTEGER,
                                      authors TEXT,
                                      venue TEXT,
                                      volume TEXT,
                                      publication_type TEXT,
                                      publication_source TEXT,
                                      processed BOOLEAN DEFAULT 0,
                                      file_path TEXT DEFAULT NULL
);

-- Table for virtual tutor assessments
CREATE TABLE IF NOT EXISTS virtual_tutor_assessments (
                                                         paper_id INTEGER PRIMARY KEY,
    -- Phase 1: Initial Filtering
                                                         is_virtual_tutor BOOLEAN,
                                                         is_implementation BOOLEAN,
    -- Phase 2: Core System Characteristics
                                                         deployment_status TEXT,
                                                         llm_model TEXT,
                                                         uses_rag TEXT,
                                                         primary_function TEXT,
                                                         subject_domain TEXT,
                                                         generates_assessments TEXT,
    -- Phase 3: Publication Metadata
                                                         publication_type TEXT,
                                                         availability TEXT,
    -- Phase 4: Technical Architecture
                                                         lms_integration TEXT,
    -- Phase 5: Pedagogical Features
                                                         personalization TEXT,
                                                         supports_collaboration TEXT,
    -- Phase 6: Evaluation Details
                                                         empirical_evaluation TEXT,
                                                         sample_size TEXT,
                                                         evaluation_duration TEXT,
    -- Phase 7: Implementation Context
                                                         institution_type TEXT,
                                                         development_approach TEXT,
                                                         language_support TEXT,
    -- Phase 8: Additional Considerations
                                                         privacy_protection TEXT,
                                                         cost_requirements TEXT,
                                                         reference_architecture TEXT,
    -- Metadata
                                                         assessment_date TIMESTAMP,
                                                         FOREIGN KEY (paper_id) REFERENCES papers (id)
);

-- Table for keywords
CREATE TABLE IF NOT EXISTS keywords (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        keyword TEXT UNIQUE
);

-- Relationship table for keywords and papers (many-to-many)
CREATE TABLE IF NOT EXISTS rel_keywords_papers (
                                                   paper_id INTEGER,
                                                   keyword_id INTEGER,
                                                   PRIMARY KEY (paper_id, keyword_id),
                                                   FOREIGN KEY (paper_id) REFERENCES papers (id) ON DELETE CASCADE,
                                                   FOREIGN KEY (keyword_id) REFERENCES keywords (id) ON DELETE CASCADE
);

-- Normalized tables for list fields from assessments
-- These tables store multi-valued attributes from the assessment phases

-- Phase 4: Architecture components (multiple per paper)
CREATE TABLE IF NOT EXISTS assessment_architecture_components (
                                                                  paper_id INTEGER,
                                                                  component TEXT,
                                                                  PRIMARY KEY (paper_id, component),
                                                                  FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- Phase 4: Interaction modalities (multiple per paper)
CREATE TABLE IF NOT EXISTS assessment_interaction_modalities (
                                                                 paper_id INTEGER,
                                                                 modality TEXT,
                                                                 PRIMARY KEY (paper_id, modality),
                                                                 FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- Phase 4: Analytics features (multiple per paper)
CREATE TABLE IF NOT EXISTS assessment_analytics_features (
                                                             paper_id INTEGER,
                                                             feature TEXT,
                                                             PRIMARY KEY (paper_id, feature),
                                                             FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- Phase 5: Pedagogical features (multiple per paper)
CREATE TABLE IF NOT EXISTS assessment_pedagogical_features (
                                                               paper_id INTEGER,
                                                               feature TEXT,
                                                               PRIMARY KEY (paper_id, feature),
                                                               FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- Phase 5: Collaboration types (multiple per paper)
CREATE TABLE IF NOT EXISTS assessment_collaboration_types (
                                                              paper_id INTEGER,
                                                              collaboration_type TEXT,
                                                              PRIMARY KEY (paper_id, collaboration_type),
                                                              FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- Phase 6: Aspects evaluated (multiple per paper)
CREATE TABLE IF NOT EXISTS assessment_aspects_evaluated (
                                                            paper_id INTEGER,
                                                            aspect TEXT,
                                                            PRIMARY KEY (paper_id, aspect),
                                                            FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(publication_year);
CREATE INDEX IF NOT EXISTS idx_papers_processed ON papers(processed);
CREATE INDEX IF NOT EXISTS idx_papers_source ON papers(publication_source);

CREATE INDEX IF NOT EXISTS idx_assessments_virtual_tutor ON virtual_tutor_assessments(is_virtual_tutor);
CREATE INDEX IF NOT EXISTS idx_assessments_implementation ON virtual_tutor_assessments(is_implementation);
CREATE INDEX IF NOT EXISTS idx_assessments_llm_model ON virtual_tutor_assessments(llm_model);
CREATE INDEX IF NOT EXISTS idx_assessments_evaluation ON virtual_tutor_assessments(empirical_evaluation);

CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_rel_kp_paper ON rel_keywords_papers(paper_id);
CREATE INDEX IF NOT EXISTS idx_rel_kp_keyword ON rel_keywords_papers(keyword_id);

-- Views for common queries

-- View combining papers with their assessment status
CREATE VIEW IF NOT EXISTS papers_with_assessment_status AS
SELECT
    p.*,
    a.is_virtual_tutor,
    a.is_implementation,
    a.llm_model,
    a.primary_function,
    a.empirical_evaluation,
    a.assessment_date,
    CASE
        WHEN a.paper_id IS NULL THEN 'Unassessed'
        WHEN a.is_virtual_tutor = 1 THEN 'Virtual Tutor'
        ELSE 'Not Virtual Tutor'
        END as assessment_status
FROM papers p
         LEFT JOIN virtual_tutor_assessments a ON p.id = a.paper_id;

-- View for papers with implementation details
CREATE VIEW IF NOT EXISTS implementation_papers AS
SELECT
    p.*,
    a.*
FROM papers p
         INNER JOIN virtual_tutor_assessments a ON p.id = a.paper_id
WHERE a.is_implementation = 1;

-- View for keyword frequency analysis
CREATE VIEW IF NOT EXISTS keyword_frequency AS
SELECT
    k.keyword,
    COUNT(r.paper_id) as paper_count
FROM keywords k
         LEFT JOIN rel_keywords_papers r ON k.id = r.keyword_id
GROUP BY k.id, k.keyword
ORDER BY paper_count DESC;
