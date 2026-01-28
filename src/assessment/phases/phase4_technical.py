"""
Phase 4: Technical Architecture
Batch processing for Q14-Q17
Skip entire phase if Q2 = No (theoretical papers)
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase4Technical
from pydantic import BaseModel


class Phase4Processor(PhaseProcessor):
    """
    Phase4Processor is a concrete implementation of PhaseProcessor.

    This class is used to process and manage phase 4-specific operations, including
    building phase-specific questions and generating default responses for the
    phase. It provides functionality tailored to the requirements of phase 4,
    such as handling learning analytics features, integration in LMS, architecture
    components, and interaction modalities.

    Attributes:
        model: The model associated with the processor instance, used for phase-specific tasks.
    """

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase4Technical

    def build_questions(self, **conditions) -> str:
        """
        Builds and returns a formatted string of predefined questions.

        This method compiles a list of questions and combines them into a single
        string, separated by newline characters.

        Returns:
            str: A string containing all the predefined questions, separated by
            newline characters.
        """
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
