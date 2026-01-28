"""
Phase 6: Evaluation Details
Batch processing for Q10-Q11, Q24-Q25
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase6Evaluation
from pydantic import BaseModel


class Phase6Processor(PhaseProcessor):
    """
    Phase6Processor class is a specialized extension of PhaseProcessor.

    It is designed to handle the processing and question generation for Phase 6 of some defined process. It
    utilizes a specific model and prompt template to perform its duties. The class provides methods to retrieve
    the corresponding model, build questions for the phase, and generate default responses.

    Attributes
    ----------
    None

    Methods
    -------
    get_phase_model()
        Returns the model class associated with Phase 6.

    build_questions(**conditions)
        Constructs questions specific to Phase 6 based on given conditions.

    get_default_response()
        Returns the default response for Phase 6 with preset values.
    """

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase6Evaluation

    def build_questions(self, **conditions) -> str:
        """
        Builds a list of survey questions based on provided conditions and returns them as a single
        string separated by newline characters.

        Parameters:
            **conditions: Arbitrary keyword arguments used to specify conditions for including or
            excluding certain questions. For example, 'include_evaluation_details' can determine
            whether additional questions related to evaluation details are included. Defaults to True.

        Returns:
            str: A string of questions separated by newline characters.
        """
        questions = [
            "Q10. Has an empirical evaluation of the tutor been conducted?"
        ]

        # Q11, Q24, Q25 are conditional on Q10, but we'll ask them anyway
        if conditions.get('include_evaluation_details', True):
            questions.extend([
                "Q11. What aspects were evaluated? (only answer if evaluation was conducted)",
                "Q24. Sample Size (only answer if evaluation was conducted)",
                "Q25. Evaluation Duration (only answer if evaluation was conducted)"
            ])

        return "\n".join(questions)

    def get_default_response(self) -> Phase6Evaluation:
        return Phase6Evaluation(
            empirical_evaluation="not_specified",
            aspects_evaluated=None,
            sample_size=None,
            evaluation_duration=None
        )
