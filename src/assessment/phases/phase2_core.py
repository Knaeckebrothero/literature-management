"""
Phase 2: Core System Characteristics
Batch processing for Q3-Q9
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase2Core
from pydantic import BaseModel


class Phase2Processor(PhaseProcessor):
    """
    Phase2Processor class processes and handles Phase 2 operations for a given model.

    This class is a subclass of PhaseProcessor and handles specific functionality
    and requirements associated with Phase 2 of the processing lifecycle. It provides
    methods to retrieve the appropriate model for Phase 2, build questions that are relevant
    to Phase 2 conditions and scenarios, and define the default response object for Phase 2.

    Attributes:
        Inherits all public attributes from PhaseProcessor.

    Methods:
        get_phase_model:
            Retrieves the model type associated with Phase 2 operations.
        build_questions:
            Constructs and returns a string containing questions relevant to Phase 2,
            subject to given conditions.
        get_default_response:
            Returns the default Phase 2 response as a Phase2Core object.
    """

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase2Core

    def build_questions(self, **conditions) -> str:
        """
        Constructs a set of questions based on given conditions.

        This function dynamically builds a list of questions to be asked depending
        on the specified conditions. Certain questions might be included or excluded
        based on the criteria provided. The resulting questions are returned as a
        single formatted string.

        Parameters:
            conditions: Keyword arguments specifying conditions for constructing
            the questions. It determines which questions to include in the result.

        Returns:
            str: A formatted string consisting of the questions separated by newline
            characters.
        """
        questions = []

        # Q3: Only asked if is_implementation = True
        if conditions.get('is_implementation', True):
            questions.append("Q3. What is the deployment status?")

        # Q4-Q6, Q8-Q9: Always asked
        questions.extend([
            "Q4. Which LLM/AI model was used?",
            "Q5. Does the system use RAG (Retrieval-Augmented Generation)?",
            "Q6. What is the primary function of the tutor?",
            "Q8. What is the subject domain of the tutor?",
            "Q9. Is the tutor able to generate assessments?"
        ])

        return "\n".join(questions)

    def get_default_response(self) -> Phase2Core:
        return Phase2Core(
            deployment_status="not_specified",
            llm_model="not_specified",
            uses_rag="not_specified",
            primary_function="other",
            subject_domain="domain_agnostic",
            generates_assessments="not_specified"
        )
