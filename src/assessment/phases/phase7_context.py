"""
Phase 7: Implementation Context
Batch processing for Q21-Q23
Consider skipping if Q2 = No (theoretical papers)
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase7Context
from pydantic import BaseModel


class Phase7Processor(PhaseProcessor):
    """
    Represents the Phase 7 processor handling phase-specific operations.

    This class is responsible for managing and processing functionalities related
    to Phase 7 in the workflow. It inherits from the PhaseProcessor class and is
    designed to provide phase-specific operations such as fetching the related
    data model, building questions, or retrieving default responses.
    """

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase7Context

    def build_questions(self, **conditions) -> str:
        """
        Builds and returns a formatted string of predefined questions.

        This method generates a string that includes predefined survey questions.
        The method formats and combines these questions into a single string, separated
        by newline characters.

        Parameters:
            **conditions: Arbitrary keyword arguments used to apply specific conditions
                          when building questions (not utilized in the method logic).

        Returns:
            str: A formatted string containing the predefined questions, separated by
                 newline characters.
        """
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
