"""
Phase 5: Pedagogical Features
Batch processing for Q7, Q18-Q20
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase5Pedagogical
from pydantic import BaseModel


class Phase5Processor(PhaseProcessor):
    """Processor for Phase 5: Pedagogical Features"""

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase5Pedagogical

    def build_questions(self, **conditions) -> str:
        """Build questions for Phase 5"""
        questions = [
            "Q7. Which specific pedagogical features are implemented? (select multiple if applicable)",
            "Q18. Does the system adapt to individual learners?",
            "Q19. Does the system support collaborative learning?"
        ]

        # Q20 is conditional on Q19 = Yes, but we'll ask it anyway and handle in post-processing
        if conditions.get('include_collaboration_types', True):
            questions.append("Q20. What type of collaborative learning? (only answer if Q19 is Yes)")

        return "\n".join(questions)

    def get_default_response(self) -> Phase5Pedagogical:
        return Phase5Pedagogical(
            pedagogical_features=["none_specified"],
            personalization="not_specified",
            supports_collaboration="not_specified",
            collaboration_types=None
        )
