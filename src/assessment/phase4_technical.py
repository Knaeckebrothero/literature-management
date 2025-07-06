"""
Phase 4: Technical Architecture
Batch processing for Q14-Q17
Skip entire phase if Q2 = No (theoretical papers)
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase4Technical
from pydantic import BaseModel


class Phase4Processor(PhaseProcessor):
    """Processor for Phase 4: Technical Architecture"""

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase4Technical

    def build_questions(self, **conditions) -> str:
        """Build questions for Phase 4"""
        questions = [
            "Q14. Integration in LMS",
            "Q15. Functional patterns/Architecture components (select multiple if applicable)",
            "Q16. Interaction Modality (select multiple if applicable)",
            "Q17. Learning Analytics Features (select multiple if applicable)"
        ]
        return "\n".join(questions)

    def get_default_response(self) -> Phase4Technical:
        return Phase4Technical(
            lms_integration="not_specified",
            architecture_components=["not_specified"],
            interaction_modality=["not_specified"],
            analytics_features=["none_mentioned"]
        )
