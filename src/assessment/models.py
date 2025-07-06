"""
Data models for Virtual Tutor Assessment phases
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, List


# Phase 1: Initial Filtering
class Phase1Filtering(BaseModel):
    is_virtual_tutor: bool = Field(
        description="Is the paper about a Virtual Tutor?"
    )
    is_implementation: bool = Field(
        description="Is the paper about the implementation of a virtual tutor?",
        default=False
    )


# Phase 2: Core System Characteristics
class Phase2Core(BaseModel):
    deployment_status: Optional[Literal[
        "research_prototype", "pilot_deployment", "production_use",
        "discontinued", "not_specified"
    ]] = Field(
        description="What is the deployment status?",
        default=None
    )
    llm_model: Literal[
        "gpt_35_4", "claude", "llama", "bert", "t5", "gemini",
        "custom_finetuned", "multiple_models", "not_specified"
    ] = Field(
        description="Which LLM/AI model was used?"
    )
    uses_rag: Literal["yes", "no", "not_specified"] = Field(
        description="Does the system use RAG?"
    )
    primary_function: Literal[
        "qa", "feedback_assignments", "exam_prep", "content_explanation",
        "learning_motivation", "exercise_generation", "multiple_functions", "other"
    ] = Field(
        description="What is the primary function of the tutor?"
    )
    subject_domain: Literal[
        "computer_science", "mathematics", "natural_sciences", "engineering",
        "languages", "social_sciences", "multiple_domains", "domain_agnostic"
    ] = Field(
        description="What is the subject domain of the tutor?"
    )
    generates_assessments: Literal["yes", "no", "not_specified"] = Field(
        description="Is the tutor able to generate assessments?"
    )


# Phase 3: Publication Metadata
class Phase3Metadata(BaseModel):
    publication_type: Literal[
        "journal_article", "conference_paper", "technical_report",
        "thesis_dissertation", "preprint", "other"
    ] = Field(
        description="Type and extent of publication"
    )
    availability: Literal[
        "freely_available", "available_on_request", "commercial_license",
        "internal_use_only", "not_available", "not_specified"
    ] = Field(
        description="Degree of availability"
    )


# Phase 4: Technical Architecture
class Phase4Technical(BaseModel):
    lms_integration: Literal[
        "moodle", "canvas", "other_lms", "standalone",
        "api_based", "not_specified"
    ] = Field(
        description="Integration in LMS"
    )
    architecture_components: List[Literal[
        "knowledge_graph", "learning_analytics", "feedback_mechanisms",
        "user_modeling", "evaluation_systems", "multiple_components", "not_specified"
    ]] = Field(
        description="Functional patterns/Architecture components"
    )
    interaction_modality: List[Literal[
        "text_only", "voice", "multimodal", "code_execution",
        "file_upload_download", "not_specified"
    ]] = Field(
        description="Interaction Modality"
    )
    analytics_features: List[Literal[
        "progress_tracking", "pattern_analysis", "performance_prediction",
        "recommendation_system", "dashboard", "none_mentioned"
    ]] = Field(
        description="Learning Analytics Features"
    )


# Phase 5: Pedagogical Features
class Phase5Pedagogical(BaseModel):
    pedagogical_features: List[Literal[
        "paraphrasing", "translation", "correction", "summary_generation",
        "concept_explanation", "example_generation", "step_by_step_guidance",
        "none_specified"
    ]] = Field(
        description="Which specific pedagogical features are implemented?"
    )
    personalization: Literal[
        "personalized_learning_paths", "adaptive_feedback", "learner_modeling",
        "no_personalization", "not_specified"
    ] = Field(
        description="Does the system adapt to individual learners?"
    )
    supports_collaboration: Literal["yes", "no", "not_specified"] = Field(
        description="Does the system support collaborative learning?"
    )
    collaboration_types: Optional[List[Literal[
        "group_discussions", "peer_review", "shared_workspaces",
        "team_projects", "social_learning", "not_applicable"
    ]]] = Field(
        description="What type of collaborative learning?",
        default=None
    )


# Phase 6: Evaluation Details
class Phase6Evaluation(BaseModel):
    empirical_evaluation: Literal[
        "controlled_experiment", "pilot_study", "survey_only",
        "no_evaluation", "not_specified"
    ] = Field(
        description="Has an empirical evaluation been conducted?"
    )
    aspects_evaluated: Optional[List[Literal[
        "academic_performance", "student_engagement", "learning_satisfaction",
        "knowledge_retention", "self_regulated_learning", "multiple_outcomes",
        "none_measured", "not_applicable"
    ]]] = Field(
        description="What aspects were evaluated?",
        default=None
    )
    sample_size: Optional[Literal[
        "less_than_50", "50_to_200", "201_to_500", "more_than_500",
        "not_reported", "no_evaluation"
    ]] = Field(
        description="Sample Size",
        default=None
    )
    evaluation_duration: Optional[Literal[
        "single_session", "less_than_month", "one_semester",
        "multiple_semesters", "longitudinal", "not_specified"
    ]] = Field(
        description="Evaluation Duration",
        default=None
    )


# Phase 7: Implementation Context
class Phase7Context(BaseModel):
    institution_type: Literal[
        "research_university", "applied_sciences", "technical_university",
        "private_institution", "multiple_types", "not_specified"
    ] = Field(
        description="Institution Type"
    )
    development_approach: Literal[
        "in_house", "commercial", "open_source", "research_prototype",
        "hybrid", "not_specified"
    ] = Field(
        description="Development Approach"
    )
    language_support: Literal[
        "german_only", "english_only", "multilingual", "not_specified"
    ] = Field(
        description="Language Support"
    )


# Phase 8: Additional Considerations
class Phase8Additional(BaseModel):
    privacy_protection: Literal[
        "gdpr_discussed", "data_protection_described",
        "privacy_addressed", "not_mentioned"
    ] = Field(
        description="Privacy/Data Protection Mentioned"
    )
    cost_requirements: Literal[
        "free", "subscription", "one_time_license",
        "infrastructure_costs_discussed", "not_discussed"
    ] = Field(
        description="Cost/Resource Requirements"
    )
    reference_architecture: Literal[
        "specific_cited", "general_patterns", "no_reference", "not_clear"
    ] = Field(
        description="Reference Architecture Mentioned"
    )


# Complete Assessment Result
class VirtualTutorAssessmentResult(BaseModel):
    phase1: Phase1Filtering
    phase2: Optional[Phase2Core] = None
    phase3: Optional[Phase3Metadata] = None
    phase4: Optional[Phase4Technical] = None
    phase5: Optional[Phase5Pedagogical] = None
    phase6: Optional[Phase6Evaluation] = None
    phase7: Optional[Phase7Context] = None
    phase8: Optional[Phase8Additional] = None
