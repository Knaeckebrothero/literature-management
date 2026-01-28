"""
Phase 3: Publication Metadata
Batch processing for Q12-Q13
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase3Metadata
from pydantic import BaseModel


class Phase3Processor(PhaseProcessor):
    """
    Process and manage operations specific to Phase 3.

    This class extends the PhaseProcessor base class and implements behaviors
    specific to Phase 3 operations. It utilizes a given model and the Phase 3
    prompt template for its functionality. This class is responsible for building
    Phase 3 questions, managing default responses, and providing the corresponding
    Phase model.
    """

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase3Metadata

    def build_questions(self, **conditions) -> str:
        """
        Generates a formatted string containing a list of predefined questions based on given conditions.

        Parameters:
        conditions: dict
            A dictionary of conditions that might determine the selection or formatting
            of the questions. This is currently unused in the method.

        Returns:
        str
            A string where each question is formatted on a new line.
        """
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
