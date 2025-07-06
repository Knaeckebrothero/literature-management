"""
Data models for Virtual Tutor Assessment phases
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, List


# Phase 1: Initial Filtering
class Phase1Filtering(BaseModel):
    is_virtual_tutor: bool = Field(
        description="""Determine if this paper primarily focuses on an AI-based educational system that meets ALL of the following criteria:

    REQUIRED CHARACTERISTICS:
    1. Uses natural language processing (NLP) or large language models (LLMs) to interact with learners
    2. Operates in a higher education context (universities, colleges, or equivalent post-secondary institutions)
    3. Provides educational support through conversational or interactive means
    4. Has an explicit tutoring, teaching, or learning support purpose

    INCLUDES:
    - Chatbots designed for educational purposes in universities
    - LLM-based teaching assistants or tutoring systems
    - Conversational agents for learning support
    - AI tutors, virtual teaching assistants, or pedagogical agents
    - Systems using GPT, BERT, LLaMA, or similar language models for education

    EXCLUDES:
    - General-purpose chatbots not specifically designed for education
    - K-12 or primary/secondary education systems
    - Non-conversational educational tools (e.g., automated grading only)
    - Traditional intelligent tutoring systems without NLP/LLM components
    - Pure information retrieval systems without tutoring capabilities
    - Administrative chatbots (enrollment, scheduling) without learning support

    The paper's main focus must be on such a system, not merely mentioned in passing."""
    )
    is_implementation: bool = Field(
        description="""Determine if this paper describes the actual development, deployment, or empirical evaluation of a virtual tutor system (not just theoretical discussion).

    IMPLEMENTATION INDICATORS:
    - Technical architecture or system design details
    - Implementation methodology or development process
    - Code, algorithms, or technical specifications
    - Deployment in a real educational setting (pilot or production)
    - Empirical evaluation with actual users/students
    - Performance metrics or usage data from a real system
    - Case study of an actual implementation

    THEORETICAL/CONCEPTUAL INDICATORS:
    - Theoretical frameworks or conceptual models without implementation
    - Literature reviews or surveys without original system development
    - Position papers or opinion pieces about virtual tutors
    - Requirements analysis without actual system building
    - Proposed designs without implementation details
    - General discussions about AI in education without specific system

    Note: A paper describes an implementation if something was actually built (even a prototype), not just proposed."""
    )

# Phase 2: Core System Characteristics
class Phase2Core(BaseModel):
    deployment_status: Optional[Literal[
        "research_prototype", "pilot_deployment", "production_use",
        "discontinued", "not_specified"
    ]] = Field(
        description="""Identify the current deployment status of the virtual tutor system.

    RESEARCH PROTOTYPE:
    - Proof-of-concept or experimental system
    - Used only by researchers or in controlled lab settings
    - Not available to regular students/courses
    - Primarily for testing ideas or demonstrating feasibility

    PILOT DEPLOYMENT:
    - Limited deployment in real educational settings
    - Used by a small group of actual students/courses
    - Testing phase before wider rollout
    - May be labeled as "beta", "trial", or "pilot study"

    PRODUCTION USE:
    - Fully deployed and regularly used system
    - Available to all relevant students/courses
    - Integrated into normal educational operations
    - Past the experimental/testing phase

    DISCONTINUED:
    - System was deployed but is no longer in use
    - Project ended or was abandoned
    - Explicitly stated as discontinued or deprecated

    NOT SPECIFIED:
    - Paper does not clearly indicate deployment status
    - Ambiguous or missing information about current use""",
        default=None
    )

    # TODO: Make this a free text field (perhaps with a validation regex?)
    llm_model: Literal[
        "gpt_35_4", "claude", "llama", "bert", "t5", "gemini",
        "custom_finetuned", "multiple_models", "not_specified"
    ] = Field(
        description="""Identify the primary language model or AI technology powering the virtual tutor.

    GPT_35_4: Any GPT-3.5 or GPT-4 variant (including ChatGPT, text-davinci, gpt-3.5-turbo, gpt-4)
    CLAUDE: Any Anthropic Claude model
    LLAMA: Meta's LLaMA models (including Alpaca, Vicuna, or other LLaMA derivatives)
    BERT: BERT or BERT-based models (RoBERTa, DistilBERT, ALBERT, etc.)
    T5: T5 or similar encoder-decoder models (BART, mT5, etc.)
    GEMINI: Google's Gemini models (formerly Bard)
    CUSTOM_FINETUNED: 
        - Fine-tuned version of a base model specifically for this application
        - Custom-trained model from scratch
        - Significantly modified architecture
    MULTIPLE_MODELS: 
        - System uses multiple different LLMs
        - Ensemble or hybrid approach
        - Different models for different functions
    NOT_SPECIFIED: Model details not provided or unclear

    Note: If a fine-tuned version of a standard model (e.g., fine-tuned GPT-3) is used, select the base model category unless the fine-tuning is extensively discussed as a key contribution."""
    )
    uses_rag: Literal["yes", "no", "not_specified"] = Field(
        description="""Determine if the system uses Retrieval-Augmented Generation or similar retrieval mechanisms.

    YES - System includes:
    - Explicit mention of RAG, retrieval-augmented generation
    - Vector database for document retrieval (Pinecone, Weaviate, ChromaDB, etc.)
    - Embedding-based search for relevant content
    - Knowledge base that is searched before generating responses
    - Document retrieval + LLM generation pipeline
    - Semantic search over course materials

    NO - System clearly:
    - Uses only the base LLM without external knowledge retrieval
    - Relies solely on model's pre-trained knowledge
    - Has no document/database search component
    - Explicitly states it doesn't use retrieval

    NOT SPECIFIED:
    - Architecture details insufficient to determine
    - No clear mention of retrieval mechanisms
    - Ambiguous whether external knowledge is used"""
    )
    primary_function: Literal[
        "qa", "feedback_assignments", "exam_prep", "content_explanation",
        "learning_motivation", "exercise_generation", "multiple_functions", "other"
    ] = Field(
        description="""Identify the main educational function of the virtual tutor.

    QA: Question answering
        - Responds to student questions about course material
        - FAQ-style interactions
        - Clarification of concepts through Q&A

    FEEDBACK_ASSIGNMENTS: Assignment/homework feedback
        - Reviews student submissions
        - Provides feedback on essays, code, or solutions
        - Grading assistance or automated feedback

    EXAM_PREP: Exam preparation
        - Practice questions for tests
        - Review sessions for exams
        - Mock examinations or quizzes

    CONTENT_EXPLANATION: Content explanation
        - Explains course concepts in detail
        - Provides examples and elaborations
        - Acts as supplementary lecturer

    LEARNING_MOTIVATION: Learning motivation
        - Encourages student engagement
        - Provides motivational support
        - Tracks and encourages progress

    EXERCISE_GENERATION: Exercise/problem generation
        - Creates practice problems
        - Generates personalized exercises
        - Adapts difficulty to student level

    MULTIPLE_FUNCTIONS: Combines several of above
        - No single primary function
        - Comprehensive tutoring system

    OTHER: Primary function not listed above"""
    )
    subject_domain: Literal[
        "computer_science", "mathematics", "natural_sciences", "engineering",
        "languages", "social_sciences", "multiple_domains", "domain_agnostic"
    ] = Field(
        description="""Identify the academic subject area where the virtual tutor operates.

    COMPUTER_SCIENCE:
        - Programming courses
        - Software engineering
        - Data structures, algorithms
        - AI/ML, databases, networks

    MATHEMATICS:
        - Calculus, linear algebra
        - Statistics, probability
        - Pure or applied mathematics

    NATURAL_SCIENCES:
        - Physics, chemistry, biology
        - Earth sciences, astronomy
        - Laboratory courses

    ENGINEERING:
        - Mechanical, electrical, civil
        - Chemical, aerospace
        - Any engineering discipline

    LANGUAGES:
        - Foreign language learning
        - Linguistics
        - Writing/composition courses

    SOCIAL_SCIENCES:
        - Psychology, sociology
        - Economics, political science
        - History, anthropology

    MULTIPLE_DOMAINS:
        - Explicitly designed for multiple subjects
        - Tested across different disciplines

    DOMAIN_AGNOSTIC:
        - Generic system adaptable to any subject
        - No specific domain mentioned
        - Framework without domain specialization"""
    )
    generates_assessments: Literal["yes", "no", "not_specified"] = Field(
        description="""Determine if the virtual tutor can create assessments, quizzes, or tests for students.

    YES - System can:
        - Generate quiz questions
        - Create practice tests
        - Produce exercises with solutions
        - Design assessments based on learning objectives
        - Create personalized problem sets
        - Generate multiple choice, short answer, or essay questions

    NO - System:
        - Only answers questions, doesn't create them
        - Explicitly stated as not generating assessments
        - Limited to explanation and feedback only

    NOT SPECIFIED:
        - No mention of assessment generation capability
        - Unclear if this feature exists"""
    )


# Phase 3: Publication Metadata
class Phase3Metadata(BaseModel):
    publication_type: Literal[
        "journal_article", "conference_paper", "technical_report",
        "thesis_dissertation", "preprint", "other"
    ] = Field(
        description="""Identify the type of publication for proper categorization in the systematic review.

    JOURNAL_ARTICLE:
        - Peer-reviewed journal publication
        - Published in academic journals (e.g., IEEE Transactions, ACM journals)
        - Includes both regular and special issue articles
        - Look for: volume/issue numbers, DOI, journal name

    CONFERENCE_PAPER:
        - Full conference proceedings paper
        - Workshop papers at major conferences
        - Symposium publications
        - Look for: conference name, location, dates, "Proceedings of..."

    TECHNICAL_REPORT:
        - University or research institution reports
        - White papers from research groups
        - Project deliverables or documentation
        - Not peer-reviewed through traditional venues

    THESIS_DISSERTATION:
        - Master's thesis
        - Doctoral dissertation
        - PhD thesis
        - Look for: degree type, university name, advisor mentioned

    PREPRINT:
        - ArXiv, bioRxiv, or other preprint servers
        - Papers explicitly marked as preprints
        - Not yet peer-reviewed versions
        - Look for: "preprint", arXiv ID, "submitted to..."

    OTHER:
        - Book chapters
        - Magazine articles
        - Blog posts or online articles
        - Anything not fitting above categories"""
    )
    availability: Literal[
        "freely_available", "available_on_request", "commercial_license",
        "internal_use_only", "not_available", "not_specified"
    ] = Field(
        description="""Determine the availability of the virtual tutor system described in the paper.

    FREELY_AVAILABLE:
        - Open source with code on GitHub/GitLab/etc.
        - Publicly accessible web application
        - Free download without registration
        - Explicitly stated as open source or freely available
        - Look for: repository links, "available at", open source licenses

    AVAILABLE_ON_REQUEST:
        - Authors offer access upon request
        - Demo available by contacting authors
        - Code/system shared for research purposes
        - Look for: "contact authors for access", "available upon request"

    COMMERCIAL_LICENSE:
        - Paid product or service
        - Commercial software requiring purchase
        - Subscription-based access
        - Part of commercial LMS or platform
        - Look for: pricing, licensing terms, company names

    INTERNAL_USE_ONLY:
        - Only for specific institution's students/staff
        - Restricted to organization members
        - Not available to external users
        - Look for: "internal system", "for our students only"

    NOT_AVAILABLE:
        - Explicitly stated as not available
        - Proprietary without access options
        - Discontinued with no archives
        - Look for: "not publicly available", "proprietary"

    NOT_SPECIFIED:
        - No information about availability
        - Unclear access status
        - Paper focuses on research without mentioning system access"""
    )


# Phase 4: Technical Architecture
class Phase4Technical(BaseModel):
    # TODO: Make this a free text field (perhaps with a validation regex?)
    lms_integration: Literal[
        "moodle", "canvas", "other_lms", "standalone",
        "api_based", "not_specified"
    ] = Field(
        description="""Identify how the virtual tutor integrates with Learning Management Systems or operates independently.

    MOODLE:
        - Moodle plugin or module
        - Integrated within Moodle interface
        - Uses Moodle APIs or database
        - Appears as Moodle activity or resource

    CANVAS:
        - Canvas LTI integration
        - Canvas app or plugin
        - Built for Canvas ecosystem
        - Uses Canvas APIs

    OTHER_LMS:
        - Blackboard, Brightspace, Sakai, etc.
        - Any LMS not listed above
        - Custom institutional LMS
        - Look for: specific LMS name mentioned

    STANDALONE:
        - Independent web application
        - Separate mobile app
        - No LMS integration
        - Users access directly, not through LMS

    API_BASED:
        - Connects via APIs to multiple systems
        - LTI (Learning Tools Interoperability) standard
        - Agnostic integration approach
        - Can work with various LMS platforms

    NOT_SPECIFIED:
        - Integration approach unclear
        - No mention of LMS relationship
        - Technical details insufficient"""
    )
    architecture_components: List[Literal[
        "knowledge_graph", "learning_analytics", "feedback_mechanisms",
        "user_modeling", "evaluation_systems", "multiple_components", "not_specified"
    ]] = Field(
        description="""Identify ALL architectural components or design patterns used in the virtual tutor system.

    KNOWLEDGE_GRAPH:
        - Ontologies for domain knowledge
        - Concept maps or semantic networks
        - Knowledge representation structures
        - Graph databases for content relationships
        - Structured domain models

    LEARNING_ANALYTICS:
        - Student progress tracking
        - Learning behavior analysis
        - Performance dashboards
        - Data mining on student interactions
        - Predictive analytics for at-risk students

    FEEDBACK_MECHANISMS:
        - Automated feedback generation
        - Rubric-based assessment
        - Error diagnosis and correction
        - Hint generation systems
        - Scaffolding mechanisms

    USER_MODELING:
        - Student profile creation
        - Learning style adaptation
        - Knowledge state tracking
        - Personalization engines
        - Individual learner models

    EVALUATION_SYSTEMS:
        - Automated grading components
        - Assessment engines
        - Competency evaluation
        - Learning outcome measurement
        - Progress assessment tools

    MULTIPLE_COMPONENTS:
        - Select when 3 or more above components are present
        - Indicates comprehensive architecture

    NOT_SPECIFIED:
        - Architecture details not provided
        - Only include if no other components identified

    Note: Select ALL that apply. This is a multiple-choice field."""
    )
    interaction_modality: List[Literal[
        "text_only", "voice", "multimodal", "code_execution",
        "file_upload_download", "not_specified"
    ]] = Field(
        description="""Identify ALL ways students can interact with the virtual tutor.

    TEXT_ONLY:
        - Chat interface
        - Text input/output only
        - Written conversations
        - No multimedia support

    VOICE:
        - Speech recognition input
        - Voice synthesis output
        - Audio conversations
        - Voice commands

    MULTIMODAL:
        - Combines text with images
        - Diagram understanding/generation
        - Mathematical notation support
        - Rich media interactions
        - Screen sharing or annotations

    CODE_EXECUTION:
        - Can run/test code
        - Programming environment integration
        - Code compilation and feedback
        - Interactive coding support
        - REPL (Read-Eval-Print Loop) capabilities

    FILE_UPLOAD_DOWNLOAD:
        - Students can upload documents
        - Assignment submission features
        - Resource download capability
        - File sharing functionality

    NOT_SPECIFIED:
        - Interaction methods unclear
        - Only include if no other modalities identified

    Note: Select ALL that apply. Most systems support multiple modalities."""
    )
    analytics_features: List[Literal[
        "progress_tracking", "pattern_analysis", "performance_prediction",
        "recommendation_system", "dashboard", "none_mentioned"
    ]] = Field(
        description="""Identify ALL learning analytics capabilities of the virtual tutor system.

    PROGRESS_TRACKING:
        - Monitors student advancement
        - Completion rates
        - Time spent on tasks
        - Topic mastery tracking
        - Learning milestone monitoring

    PATTERN_ANALYSIS:
        - Identifies learning patterns
        - Common misconception detection
        - Interaction pattern mining
        - Learning pathway analysis
        - Behavioral pattern recognition

    PERFORMANCE_PREDICTION:
        - Predicts student outcomes
        - Early warning systems
        - Risk assessment
        - Grade prediction
        - Success likelihood estimation

    RECOMMENDATION_SYSTEM:
        - Suggests learning resources
        - Personalized content recommendations
        - Next-step guidance
        - Adaptive learning paths
        - Study strategy suggestions

    DASHBOARD:
        - Visual analytics for instructors
        - Student progress visualization
        - Class-level insights
        - Real-time monitoring interfaces
        - Data visualization tools

    NONE_MENTIONED:
        - No analytics features described
        - System lacks analytics capabilities
        - Only select if no other features apply

    Note: Select ALL that apply. Modern systems often include multiple analytics features."""
    )


# Phase 5: Pedagogical Features
class Phase5Pedagogical(BaseModel):
    pedagogical_features: List[Literal[
        "paraphrasing", "translation", "correction", "summary_generation",
        "concept_explanation", "example_generation", "step_by_step_guidance",
        "none_specified"
    ]] = Field(
        description="""Identify ALL pedagogical support features implemented in the virtual tutor.

    PARAPHRASING:
        - Restates content in simpler terms
        - Multiple explanations of same concept
        - Adapts language complexity to student level
        - "Explain like I'm five" functionality
        - Simplification of technical jargon

    TRANSLATION:
        - Language translation capabilities
        - Multilingual support
        - Cross-language learning assistance
        - Technical term translation
        - Not just UI translation, but content translation

    CORRECTION:
        - Error correction in student work
        - Grammar/syntax checking
        - Misconception correction
        - Code debugging assistance
        - Mathematical error identification

    SUMMARY_GENERATION:
        - Creates summaries of lectures/texts
        - Key point extraction
        - Study guide generation
        - Condensed explanations
        - Chapter/topic summaries

    CONCEPT_EXPLANATION:
        - Detailed concept breakdowns
        - Theoretical background provision
        - Definition clarification
        - Conceptual relationship explanation
        - Deep-dive explanations on demand

    EXAMPLE_GENERATION:
        - Creates relevant examples
        - Generates practice scenarios
        - Provides concrete illustrations
        - Context-specific examples
        - Counter-examples for clarification

    STEP_BY_STEP_GUIDANCE:
        - Breaks down complex procedures
        - Scaffolded problem solving
        - Guided walkthroughs
        - Progressive hint systems
        - Structured learning sequences

    NONE_SPECIFIED:
        - No pedagogical features described
        - Only select if no other features identified

    Note: Select ALL that apply. These align with pedagogical support mentioned in research objectives."""
    )
    personalization: Literal[
        "personalized_learning_paths", "adaptive_feedback", "learner_modeling",
        "no_personalization", "not_specified"
    ] = Field(
        description="""Determine the type of personalization or adaptation to individual learners.

    PERSONALIZED_LEARNING_PATHS:
        - Creates custom learning sequences
        - Adapts content order based on progress
        - Recommends different materials per student
        - Adjusts curriculum pacing
        - Individual learning trajectories

    ADAPTIVE_FEEDBACK:
        - Feedback varies by student level
        - Adjusts explanation depth
        - Modifies hint specificity
        - Personalizes encouragement/motivation
        - Context-aware responses

    LEARNER_MODELING:
        - Maintains student knowledge models
        - Tracks individual competencies
        - Models learning styles
        - Predicts individual needs
        - Comprehensive learner profiles

    NO_PERSONALIZATION:
        - Same experience for all users
        - No adaptation mechanisms
        - Explicitly stated as non-adaptive
        - One-size-fits-all approach

    NOT_SPECIFIED:
        - Personalization unclear
        - No mention of adaptation
        - Insufficient detail to determine

    Note: Choose the MOST sophisticated form if multiple apply."""
    )
    supports_collaboration: Literal["yes", "no", "not_specified"] = Field(
        description="""Determine if the virtual tutor facilitates collaboration between students.

    YES - System includes features for:
        - Student-to-student interaction through the tutor
        - Group problem-solving support
        - Collaborative assignments or projects
        - Peer learning facilitation
        - Discussion forums integrated with tutor
        - Team-based learning activities
        - Shared learning spaces

    NO - System:
        - Only supports individual learning
        - No multi-user features
        - Explicitly designed for solo use
        - Lacks collaboration mechanisms

    NOT SPECIFIED:
        - Collaboration features not mentioned
        - Unclear if multi-user support exists
        - No information about peer interaction"""
    )
    collaboration_types: Optional[List[Literal[
        "group_discussions", "peer_review", "shared_workspaces",
        "team_projects", "social_learning", "not_applicable"
    ]]] = Field(
        description="""If collaboration is supported (Q19=Yes), identify ALL types of collaborative learning features.

    GROUP_DISCUSSIONS:
        - Moderated discussion forums
        - Topic-based chat rooms
        - Q&A with peer responses
        - Collaborative problem discussions
        - Tutor-facilitated group conversations

    PEER_REVIEW:
        - Student work peer assessment
        - Peer feedback mechanisms
        - Collaborative grading
        - Peer tutoring features
        - Review assignment distribution

    SHARED_WORKSPACES:
        - Collaborative document editing
        - Shared problem-solving spaces
        - Joint code development
        - Real-time collaboration tools
        - Synchronized learning environments

    TEAM_PROJECTS:
        - Project team support
        - Task distribution features
        - Team progress tracking
        - Collaborative deliverables
        - Group assignment management

    SOCIAL_LEARNING:
        - Learning communities
        - Study group formation
        - Social presence indicators
        - Peer comparison features
        - Gamification with social elements

    NOT_APPLICABLE:
        - Only select if Q19 was answered as 'No' or 'Not specified'
        - No collaboration features to categorize

    Note: Only answer if Q19=Yes. Select ALL that apply."""
    )


# Phase 6: Evaluation Details
class Phase6Evaluation(BaseModel):
    empirical_evaluation: Literal[
        "controlled_experiment", "pilot_study", "survey_only",
        "no_evaluation", "not_specified"
    ] = Field(
        description="""Identify the type of empirical evaluation conducted on the virtual tutor system.

    CONTROLLED EXPERIMENT:
        - Randomized controlled trial (RCT)
        - Control group vs. treatment group
        - Pre/post test design
        - A/B testing with statistical analysis
        - Quasi-experimental design
        - Clear hypothesis testing

    PILOT STUDY:
        - Small-scale user study
        - Feasibility or usability testing
        - Preliminary evaluation
        - Limited participant pool
        - Exploratory study
        - "Pilot", "preliminary", or "initial" evaluation

    SURVEY ONLY:
        - User satisfaction surveys
        - Perception questionnaires
        - Self-reported data only
        - No performance measurements
        - Opinion-based evaluation
        - Likert scale assessments

    NO EVALUATION:
        - No empirical study conducted
        - Only theoretical or technical description
        - System description without user testing
        - Explicitly states no evaluation done

    NOT SPECIFIED:
        - Unclear if evaluation was conducted
        - Insufficient information
        - Ambiguous methodology

    Note: Choose the MOST rigorous method if multiple evaluations were conducted."""
    )
    aspects_evaluated: Optional[List[Literal[
        "academic_performance", "student_engagement", "learning_satisfaction",
        "knowledge_retention", "self_regulated_learning", "multiple_outcomes",
        "none_measured", "not_applicable"
    ]]] = Field(
        description="""Identify ALL aspects measured in the empirical evaluation (only if Q10 indicates evaluation was done).

    ACADEMIC PERFORMANCE:
        - Test scores, grades, or GPAs
        - Problem-solving accuracy
        - Assignment quality improvements
        - Exam performance
        - Learning gain scores
        - Objective performance metrics

    STUDENT ENGAGEMENT:
        - Time spent with system
        - Interaction frequency
        - Feature usage patterns
        - Participation rates
        - Completion rates
        - Behavioral engagement metrics

    LEARNING SATISFACTION:
        - User satisfaction ratings
        - System usability scores
        - Perceived usefulness
        - User experience metrics
        - Net Promoter Score (NPS)
        - Subjective satisfaction measures

    KNOWLEDGE RETENTION:
        - Delayed post-tests
        - Long-term recall assessment
        - Transfer learning evaluation
        - Retention test scores
        - Follow-up assessments

    SELF_REGULATED_LEARNING:
        - Metacognitive skills assessment
        - Self-efficacy measures
        - Learning strategy use
        - Goal-setting behaviors
        - Self-monitoring abilities
        - Autonomy in learning

    MULTIPLE_OUTCOMES:
        - Three or more of the above categories
        - Comprehensive evaluation approach

    NONE_MEASURED:
        - Evaluation conducted but metrics unclear
        - No specific outcomes reported

    NOT_APPLICABLE:
        - Only select if Q10 = no_evaluation or not_specified

    Note: Select ALL that apply. Most evaluations measure multiple aspects."""
    )
    sample_size: Optional[Literal[
        "less_than_50", "50_to_200", "201_to_500", "more_than_500",
        "not_reported", "no_evaluation"
    ]] = Field(
        description="""Identify the total number of participants in the empirical evaluation.

    LESS_THAN_50:
        - 1-49 participants total
        - Very small studies
        - Typical for qualitative studies
        - Early pilot testing

    50_TO_200:
        - 50-200 participants
        - Small to medium studies
        - Typical for semester-long courses
        - Common in educational research

    201_TO_500:
        - 201-500 participants
        - Medium to large studies
        - Multiple classes or cohorts
        - Substantial sample size

    MORE_THAN_500:
        - Over 500 participants
        - Large-scale studies
        - MOOC-level participation
        - Multiple institutions

    NOT_REPORTED:
        - Evaluation done but sample size not stated
        - Participant count unclear
        - Missing information

    NO_EVALUATION:
        - Only select if Q10 = no_evaluation

    Note: Count ALL participants across all conditions/groups. If multiple studies reported, use the largest."""
    )
    evaluation_duration: Optional[Literal[
        "single_session", "less_than_month", "one_semester",
        "multiple_semesters", "longitudinal", "not_specified"
    ]] = Field(
        description="""Identify how long the empirical evaluation lasted.

    SINGLE_SESSION:
        - One-time use evaluation
        - Single lab session
        - Less than one day
        - Cross-sectional snapshot
        - Usability testing session

    LESS_THAN_MONTH:
        - Few days to 4 weeks
        - Short-term study
        - Module or unit-based
        - Sprint or workshop duration

    ONE_SEMESTER:
        - Full academic term
        - 3-6 months typically
        - Quarter or semester-long
        - Single course duration
        - Most common in higher ed research

    MULTIPLE_SEMESTERS:
        - 2-3 semesters
        - Full academic year
        - Multi-term evaluation
        - Extended but not longitudinal

    LONGITUDINAL:
        - Over 1 year
        - Tracks cohorts over time
        - Multiple academic years
        - Long-term impact study
        - Follow-up after course completion

    NOT_SPECIFIED:
        - Duration not clearly stated
        - Timeframe ambiguous
        - Evaluation done but length unclear

    Note: Use the active intervention period, not follow-up measurements."""
    )


# Phase 7: Implementation Context
class Phase7Context(BaseModel):
    institution_type: Literal[
        "research_university", "applied_sciences", "technical_university",
        "private_institution", "multiple_types", "not_specified"
    ] = Field(
        description="""Identify the type of higher education institution where the virtual tutor was developed or deployed.

    RESEARCH_university:
        - Traditional research universities
        - Comprehensive universities (Universität in Germany)
        - R1/R2 institutions in US
        - Focus on research and graduate programs
        - Examples: MIT, Oxford, LMU Munich

    APPLIED_SCIENCES:
        - Universities of Applied Sciences
        - Fachhochschule (FH) / Hochschule für Angewandte Wissenschaften (HAW)
        - Polytechnics
        - Practice-oriented institutions
        - Focus on professional preparation

    TECHNICAL_UNIVERSITY:
        - Technical Universities (TU/TH)
        - Institutes of Technology
        - Engineering-focused institutions
        - STEM-specialized universities
        - Examples: TU Munich, Georgia Tech, ETH Zurich

    PRIVATE_INSTITUTION:
        - Private universities or colleges
        - For-profit educational institutions
        - Non-public funding model
        - Examples: International University (IU), private business schools

    MULTIPLE_TYPES:
        - Collaboration between different institution types
        - Deployed across various institution categories
        - Multi-institutional project
        - Consortium development

    NOT_SPECIFIED:
        - Institution type not mentioned
        - Generic "university" without details
        - Cannot determine from paper

    Note: If both development and deployment institutions differ, prioritize where it's actively used."""
    )
    development_approach: Literal[
        "in_house", "commercial", "open_source", "research_prototype",
        "hybrid", "not_specified"
    ] = Field(
        description="""Identify how the virtual tutor system was developed and maintained.

    IN_HOUSE:
        - Developed by the institution's own team
        - Internal IT/education technology department
        - Faculty-led development
        - Custom built for specific institutional needs
        - Maintained by university staff

    COMMERCIAL:
        - Licensed commercial product
        - Vendor-developed solution
        - Subscription-based service
        - Third-party educational technology
        - Examples: integration of ChatGPT API, commercial LMS plugins

    OPEN_SOURCE:
        - Community-driven development
        - GitHub/GitLab hosted project
        - Open contribution model
        - Free software license (MIT, GPL, Apache)
        - Collaborative development across institutions

    RESEARCH_PROTOTYPE:
        - Developed as research project
        - Grant-funded development
        - PhD/postdoc project outcome
        - Proof-of-concept implementation
        - Academic research output

    HYBRID:
        - Combination of approaches
        - Commercial base with custom modifications
        - Open source with proprietary extensions
        - Research project becoming commercial
        - Multiple development models

    NOT_SPECIFIED:
        - Development approach unclear
        - No information about how system was built
        - Ambiguous development model"""
    )
    language_support: Literal[
        "german_only", "english_only", "multilingual", "not_specified"
    ] = Field(
        description="""Identify the natural language(s) supported by the virtual tutor for interaction with students.

    GERMAN_ONLY:
        - Exclusively German language interface
        - Content and interactions in German
        - Designed for German-speaking students
        - Common in DACH region implementations

    ENGLISH_ONLY:
        - Exclusively English language interface
        - English-only content and interactions
        - No localization for other languages
        - Common in international programs

    MULTILINGUAL:
        - Supports multiple languages
        - Language switching capability
        - Localized for different regions
        - Serves international student body
        - May include: German, English, and others

    NOT_SPECIFIED:
        - Interface language not mentioned
        - Language capabilities unclear
        - No information about localization

    Note: This refers to the language of INTERACTION with students, not the programming language or the language the paper is written in."""
    )


# Phase 8: Additional Considerations
class Phase8Additional(BaseModel):
    privacy_protection: Literal[
        "gdpr_discussed", "data_protection_described",
        "privacy_addressed", "not_mentioned"
    ] = Field(
        description="""Determine if and how the paper addresses privacy and data protection concerns.

    GDPR_DISCUSSED:
        - GDPR compliance explicitly mentioned
        - EU data protection regulations addressed
        - Lawful basis for processing discussed
        - Data subject rights considered
        - Privacy by design principles applied

    DATA_PROTECTION_DESCRIBED:
        - Technical data protection measures detailed
        - Encryption methods described
        - Data anonymization/pseudonymization
        - Access control mechanisms
        - Data retention policies
        - Security architecture explained

    PRIVACY_ADDRESSED:
        - General privacy concerns acknowledged
        - Ethical considerations discussed
        - User consent mechanisms mentioned
        - Privacy risks identified
        - Basic privacy awareness shown
        - No technical details provided

    NOT_MENTIONED:
        - No privacy discussion
        - Data protection ignored
        - No security considerations
        - Privacy implications not addressed

    Note: Choose the MOST specific category that applies. GDPR > Data Protection > Privacy."""
    )
    cost_requirements: Literal[
        "free", "subscription", "one_time_license",
        "infrastructure_costs_discussed", "not_discussed"
    ] = Field(
        description="""Identify discussions of costs, resources, or economic considerations for implementing the virtual tutor.

    FREE:
        - Explicitly stated as free to use
        - No costs for institutions or students
        - Open source with no fees
        - Grant-funded with free access
        - "Zero cost" implementation

    SUBSCRIPTION:
        - Recurring subscription model
        - Monthly/annual fees mentioned
        - Per-student pricing
        - SaaS pricing model
        - Ongoing license costs

    ONE_TIME_LICENSE:
        - Single purchase price
        - Perpetual license model
        - One-time implementation fee
        - Fixed cost deployment

    INFRASTRUCTURE_COSTS_DISCUSSED:
        - Server/hosting requirements analyzed
        - Computational resource needs
        - Staff time/training costs
        - Hidden costs identified
        - TCO (Total Cost of Ownership) discussed
        - Resource implications beyond licensing

    NOT_DISCUSSED:
        - No mention of costs
        - Economic aspects ignored
        - Resource requirements not addressed
        - Implementation costs unclear

    Note: Choose the MOST comprehensive discussion if multiple aspects mentioned."""
    )
    reference_architecture: Literal[
        "specific_cited", "general_patterns", "no_reference", "not_clear"
    ] = Field(
        description="""Determine if the paper references established architectures or design patterns for virtual tutors.

    SPECIFIC_CITED:
        - Names specific reference architectures
        - Cites IEEE/ACM/other standards
        - References established frameworks
        - Mentions ITS architecture standards
        - Uses recognized design patterns
        - Examples: "implements IEEE LTSA", "based on GIFT architecture"

    GENERAL_PATTERNS:
        - Discusses architectural patterns without specific citations
        - Mentions common components (but not formal architecture)
        - Describes typical system structures
        - References design patterns informally
        - Uses architectural concepts without formal framework

    NO_REFERENCE:
        - Novel architecture without precedent
        - No architectural patterns mentioned
        - Custom design without references
        - Explicitly states new approach

    NOT_CLEAR:
        - Architecture description too vague
        - Cannot determine if patterns used
        - Technical details insufficient
        - Ambiguous architectural discussion

    Note: This addresses Task 5 from research objectives about reference architectures."""
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
