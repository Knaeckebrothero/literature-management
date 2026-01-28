"""
Phase 1: Initial Filtering
Individual API calls for Q1 and Q2
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase1Filtering
from pydantic import BaseModel


class Phase1Processor(PhaseProcessor):
    """
    Handles the processing logic specifically for Phase 1 in the overall workflow.

    This class extends the PhaseProcessor base class to focus on managing the
    logic and data handling required for Phase 1 filtering and processing. It is
    designed to ask targeted questions specific to this phase, process the
    responses, and determine the filtering and categorization of the inputs.

    Attributes:
        model (BaseModel): The model used for Phase 1 processing.
    """

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase1Filtering

    def build_questions(self, **conditions) -> str:
        """
        Builds a sequence of questions based on specified conditions.

        Generates a set of context-dependent questions related to virtual tutors. The
        questions are dynamically constructed depending on the input conditions provided.
        The response is returned as a single formatted string with questions separated
        by newlines.

        Parameters:
        conditions: dict
            Optional keyword arguments used to control which questions are appended.
            For example, `q1_is_yes` determines whether Question 2 is included.

        Returns:
        str
            A string containing the constructed questions, each on a new line.
        """
        questions = []

        # Q1: Always asked
        questions.append("Q1. Is the paper about a Virtual Tutor?")

        # Q2: Only asked if we already know Q1 is Yes, or we're asking both
        if conditions.get('q1_is_yes', True):
            questions.append("Q2. Is the paper about the implementation of a virtual tutor?")

        return "\n".join(questions)

    def get_default_response(self) -> Phase1Filtering:
        """
        Returns a default response with preset parameters.

        Summary:
        This method generates and returns a default `Phase1Filtering` object
        with predefined values for its fields.

        Returns:
            Phase1Filtering: A default instance of the `Phase1Filtering` class with
            `is_virtual_tutor` set to False and `is_implementation` set to False.
        """
        return Phase1Filtering(
            is_virtual_tutor=False,
            is_implementation=False
        )

    def process_q1_only(self, content: str) -> bool:
        """
        Processes the content based on specific conditions and determines if the result is from a virtual tutor.

        Parameters:
        content (str): The textual content to process.

        Returns:
        bool: True if the result indicates it is from a virtual tutor, False otherwise.
        """
        result = self.process(content, q1_is_yes=False)
        return result.is_virtual_tutor
