"""
Phase 2: Core System Characteristics
Batch processing for Q3-Q9
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase2Core
from pydantic import BaseModel


class Phase2Processor(PhaseProcessor):
    """Processor for Phase 2: Core System Characteristics"""

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase2Core

    def build_questions(self, **conditions) -> str:
        """Build questions for Phase 2"""
        questions = []

        # Q3: Only asked if is_implementation = True
        if conditions.get('is_implementation', True):
            questions.append("Q3. What is the deployment status?")

        # Q4-Q6, Q8-Q9: Always asked
        questions.extend([
            "Q4. Which LLM/AI model was used?",
            "Q5. Does the system use RAG (Retrieval-Augmented Generation)?",
            "Q6. What is the primary function of the tutor?",
            "Q8. What is the subject domain of the tutor?",
            "Q9. Is the tutor able to generate assessments?"
        ])

        return "\n".join(questions)

    def get_default_response(self) -> Phase2Core:
        return Phase2Core(
            deployment_status="not_specified",
            llm_model="not_specified",
            uses_rag="not_specified",
            primary_function="other",
            subject_domain="domain_agnostic",
            generates_assessments="not_specified"
        )
