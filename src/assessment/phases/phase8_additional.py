"""
Phase 8: Additional Considerations
Batch processing for Q26-Q28
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase8Additional
from pydantic import BaseModel


class Phase8Processor(PhaseProcessor):
    """
    Handles the processing logic specific to Phase 8 of the model pipeline.

    This class serves as an implementation of the PhaseProcessor abstract class. It
    provides methods to retrieve the model associated with Phase 8, build questions
    relevant for this phase, and generate a default response.
    """

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase8Additional

    def build_questions(self, **conditions) -> str:
        """
        Build a formatted string from a predefined list of questions.

        The method processes predefined questions and combines them into a single
        string, separated by newline characters.

        Parameters:
            **conditions: Arbitrary keyword arguments, used to modify behavior
                          (not currently implemented).

        Returns:
            str: A single string where each question is separated by a newline.
        """
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
