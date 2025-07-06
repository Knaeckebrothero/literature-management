"""
Phase 8: Additional Considerations
Batch processing for Q26-Q28
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase8Additional
from pydantic import BaseModel


class Phase8Processor(PhaseProcessor):
    """Processor for Phase 8: Additional Considerations"""

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase8Additional

    def build_questions(self, **conditions) -> str:
        """Build questions for Phase 8"""
        questions = [
            "Q26. Privacy/Data Protection Mentioned",
            "Q27. Cost/Resource Requirements",
            "Q28. Reference Architecture Mentioned"
        ]
        return "\n".join(questions)

    def get_default_response(self) -> Phase8Additional:
        return Phase8Additional(
            privacy_protection="not_mentioned",
            cost_requirements="not_discussed",
            reference_architecture="not_clear"
        )
