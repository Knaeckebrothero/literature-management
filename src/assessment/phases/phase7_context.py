"""
Phase 7: Implementation Context
Batch processing for Q21-Q23
Consider skipping if Q2 = No (theoretical papers)
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase7Context
from pydantic import BaseModel


class Phase7Processor(PhaseProcessor):
    """Processor for Phase 7: Implementation Context"""

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase7Context

    def build_questions(self, **conditions) -> str:
        """Build questions for Phase 7"""
        questions = [
            "Q21. Institution Type",
            "Q22. Development Approach",
            "Q23. Language Support"
        ]
        return "\n".join(questions)

    def get_default_response(self) -> Phase7Context:
        return Phase7Context(
            institution_type="not_specified",
            development_approach="not_specified",
            language_support="not_specified"
        )
