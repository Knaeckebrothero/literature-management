"""
Phase 3: Publication Metadata
Batch processing for Q12-Q13
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase3Metadata
from pydantic import BaseModel


class Phase3Processor(PhaseProcessor):
    """Processor for Phase 3: Publication Metadata"""

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase3Metadata

    def build_questions(self, **conditions) -> str:
        """Build questions for Phase 3"""
        questions = [
            "Q12. Type and extent of publication",
            "Q13. Degree of availability"
        ]
        return "\n".join(questions)

    def get_default_response(self) -> Phase3Metadata:
        return Phase3Metadata(
            publication_type="other",
            availability="not_specified"
        )
