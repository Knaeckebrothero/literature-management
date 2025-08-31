"""
Phase 5: Pedagogical Features
Batch processing for Q7, Q18-Q20
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase5Pedagogical
from pydantic import BaseModel


class Phase5Processor(PhaseProcessor):
    """
    Phase5Processor class processes the pedagogical features of Phase 5.

    This class is responsible for managing Phase 5 logic, including handling
    pedagogical models, building relevant questions, and specifying default
    responses. It extends the generic PhaseProcessor for handling
    Phase 5-specific behavior.

    Attributes
    ----------
    model : type[BaseModel]
        The machine learning model associated with this processor.

    Methods
    -------
    get_phase_model() -> type[BaseModel]
        Specifies the model type associated with Phase 5.

    build_questions(**conditions) -> str
        Builds a list of questions specific to Phase 5, allowing conditional
        inclusion of collaborative learning types.

    get_default_response() -> Phase5Pedagogical
        Provides a default Phase5Pedagogical object with predefined responses.
    """

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase5Pedagogical

    def build_questions(self, **conditions) -> str:
        """
        Constructs and returns a list of predefined questions as a single string, based on the provided conditions.

        The method dynamically builds a set of questions related to pedagogical features, adaptive learning, and
        collaborative learning. Additionally, it conditionally includes specific questions depending on the input
        conditions, such as whether to include collaboration types. The final string contains all questions separated
        by newline characters.

        Parameters:
            conditions: Keyword arguments used to determine optional conditions. The available argument is
                include_collaboration_types (bool): Determines if collaborative learning-specific questions should
                be included.

        Returns:
            str: A newline-separated string of questions to be used for queries.
        """
        questions = [
            "Q7. Which specific pedagogical features are implemented? (select multiple if applicable)",
            "Q18. Does the system adapt to individual learners?",
            "Q19. Does the system support collaborative learning?"
        ]

        # Q20 is conditional on Q19 = Yes, but we'll ask it anyway and handle in post-processing
        if conditions.get('include_collaboration_types', True):
            questions.append("Q20. What type of collaborative learning? (only answer if Q19 is Yes)")

        return "\n".join(questions)

    def get_default_response(self) -> Phase5Pedagogical:
        return Phase5Pedagogical(
            pedagogical_features=["none_specified"],
            personalization="not_specified",
            supports_collaboration="not_specified",
            collaboration_types=None
        )
