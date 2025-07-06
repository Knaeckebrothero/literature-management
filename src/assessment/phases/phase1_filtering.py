"""
Phase 1: Initial Filtering
Individual API calls for Q1 and Q2
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase1Filtering
from pydantic import BaseModel


class Phase1Processor(PhaseProcessor):
    """Processor for Phase 1: Initial Filtering"""

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase1Filtering

    def build_questions(self, **conditions) -> str:
        """Build questions for Phase 1"""
        questions = []

        # Q1: Always asked
        questions.append("Q1. Is the paper about a Virtual Tutor?")

        # Q2: Only asked if we already know Q1 is Yes, or we're asking both
        if conditions.get('q1_is_yes', True):
            questions.append("Q2. Is the paper about the implementation of a virtual tutor?")

        return "\n".join(questions)

    def get_default_response(self) -> Phase1Filtering:
        return Phase1Filtering(
            is_virtual_tutor=False,
            is_implementation=False
        )

    def process_q1_only(self, content: str) -> bool:
        """Process only Q1 for early filtering"""
        result = self.process(content, q1_is_yes=False)
        return result.is_virtual_tutor
