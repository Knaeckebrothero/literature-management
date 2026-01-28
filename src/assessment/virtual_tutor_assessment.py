"""
Main Virtual Tutor Assessment class that orchestrates all phases
"""
import logging
from typing import Dict, Any, Optional
from assessment.models import VirtualTutorAssessmentResult
from assessment.phases.phase1_filtering import Phase1Processor
from assessment.phases.phase2_core import Phase2Processor
from assessment.phases.phase3_metadata import Phase3Processor
from assessment.phases.phase4_technical import Phase4Processor
from assessment.phases.phase5_pedagogical import Phase5Processor
from assessment.phases.phase6_evaluation import Phase6Processor
from assessment.phases.phase7_context import Phase7Processor
from assessment.phases.phase8_additional import Phase8Processor

logger = logging.getLogger(__name__)


class VirtualTutorAssessment:
    """Orchestrates the multi-phase virtual tutor assessment"""

    def __init__(self, model):
        self.model = model

        # Initialize all phase processors
        self.phase1 = Phase1Processor(model)
        self.phase2 = Phase2Processor(model)
        self.phase3 = Phase3Processor(model)
        self.phase4 = Phase4Processor(model)
        self.phase5 = Phase5Processor(model)
        self.phase6 = Phase6Processor(model)
        self.phase7 = Phase7Processor(model)
        self.phase8 = Phase8Processor(model)

        self.api_call_count = 0

    def assess_paper(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Assess a paper through all phases with conditional logic.
        Returns None if paper is not about virtual tutors.
        """
        logger.info("Starting virtual tutor assessment")
        self.api_call_count = 0

        # Phase 1: Initial Filtering
        logger.info("Phase 1: Initial filtering")
        self.api_call_count += 1
        phase1_result = self.phase1.process(content)

        if not phase1_result.is_virtual_tutor:
            logger.info("Paper is not about virtual tutors - stopping assessment")
            return None

        # Determine assessment scope based on Q2
        is_implementation = phase1_result.is_implementation
        logger.info(f"Paper is about implementation: {is_implementation}")

        # Phase 2: Core System Characteristics (always executed)
        logger.info("Phase 2: Core system characteristics")
        self.api_call_count += 1
        phase2_result = self.phase2.process(
            content,
            is_implementation=is_implementation
        )

        # Phase 3: Publication Metadata (always executed)
        logger.info("Phase 3: Publication metadata")
        self.api_call_count += 1
        phase3_result = self.phase3.process(content)

        # Phase 4: Technical Architecture (skip if theoretical paper)
        phase4_result = None
        if is_implementation:
            logger.info("Phase 4: Technical architecture")
            self.api_call_count += 1
            phase4_result = self.phase4.process(content)
        else:
            phase4_result = self.phase4.get_default_response()

        # Phase 5: Pedagogical Features (always executed)
        logger.info("Phase 5: Pedagogical features")
        self.api_call_count += 1
        phase5_result = self.phase5.process(content)

        # Phase 6: Evaluation Details (always executed)
        logger.info("Phase 6: Evaluation details")
        self.api_call_count += 1
        phase6_result = self.phase6.process(content)

        # Phase 7: Implementation Context (skip if theoretical)
        phase7_result = None
        if is_implementation:
            logger.info("Phase 7: Implementation context")
            self.api_call_count += 1
            phase7_result = self.phase7.process(content)
        else:
            phase7_result = self.phase7.get_default_response()

        # Phase 8: Additional Considerations (always executed)
        logger.info("Phase 8: Additional considerations")
        self.api_call_count += 1
        phase8_result = self.phase8.process(content)

        # Combine results from all phases
        # ... (rest of the method is unchanged)

        logger.info(f"Assessment complete. Total API calls: {self.api_call_count}")

        # Combine results into a single dictionary
        # In case of name conflicts, phases processed later will overwrite earlier ones
        # This is by design, as later phases might refine earlier data
        full_result = {
            **phase1_result.dict(),
            **phase2_result.dict(),
            **phase3_result.dict(),
            **(phase4_result.dict() if phase4_result else {}),
            **phase5_result.dict(),
            **phase6_result.dict(),
            **(phase7_result.dict() if phase7_result else {}),
            **phase8_result.dict(),
        }

        return full_result
