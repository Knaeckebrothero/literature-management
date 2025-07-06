"""
Phase 6: Evaluation Details
Batch processing for Q10-Q11, Q24-Q25
"""
from assessment.phase_processor import PhaseProcessor, PHASE_PROMPT_TEMPLATE
from assessment.models import Phase6Evaluation
from pydantic import BaseModel


class Phase6Processor(PhaseProcessor):
    """Processor for Phase 6: Evaluation Details"""

    def __init__(self, model):
        super().__init__(model, PHASE_PROMPT_TEMPLATE)

    def get_phase_model(self) -> type[BaseModel]:
        return Phase6Evaluation

    def build_questions(self, **conditions) -> str:
        """Build questions for Phase 6"""
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
