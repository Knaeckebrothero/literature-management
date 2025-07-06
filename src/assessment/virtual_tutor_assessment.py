"""
Main Virtual Tutor Assessment class that orchestrates all phases
"""
import logging
from typing import Dict, Any, Optional
from assessment.models import VirtualTutorAssessmentResult
from assessment.phase1_filtering import Phase1Processor
from assessment.phase2_core import Phase2Processor
from assessment.phase3_metadata import Phase3Processor
from assessment.phase4_technical import Phase4Processor
from assessment.phase5_pedagogical import Phase5Processor
from assessment.phase6_evaluation import Phase6Processor
from assessment.phase7_context import Phase7Processor
from assessment.phase8_additional import Phase8Processor

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

        # Phase 1: Initial Filtering (Q1 first for early exit)
        logger.info("Phase 1: Initial filtering - Q1")
        self.api_call_count += 1

        # First check Q1 only
        is_virtual_tutor = self.phase1.process_q1_only(content)
        if not is_virtual_tutor:
            logger.info("Paper is not about virtual tutors - stopping assessment")
            return None

        # Now get complete Phase 1 results (Q1 + Q2)
        logger.info("Phase 1: Getting Q2")
        self.api_call_count += 1
        phase1_result = self.phase1.process(content)

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
            logger.info("Skipping Phase 4 (theoretical paper)")

        # Phase 5: Pedagogical Features (always executed)
        logger.info("Phase 5: Pedagogical features")
        self.api_call_count += 1
        phase5_result = self.phase5.process(content)

        # Post-process Phase 5: Clear collaboration types if not supported
        if phase5_result.supports_collaboration != "yes":
            phase5_result.collaboration_types = None

        # Phase 6: Evaluation Details (always executed)
        logger.info("Phase 6: Evaluation details")
        self.api_call_count += 1
        phase6_result = self.phase6.process(content)

        # Post-process Phase 6: Clear conditional fields if no evaluation
        if phase6_result.empirical_evaluation in ["no_evaluation", "not_specified"]:
            phase6_result.aspects_evaluated = None
            phase6_result.sample_size = None
            phase6_result.evaluation_duration = None

        # Phase 7: Implementation Context (skip if theoretical paper)
        phase7_result = None
        if is_implementation:
            logger.info("Phase 7: Implementation context")
            self.api_call_count += 1
            phase7_result = self.phase7.process(content)
        else:
            logger.info("Skipping Phase 7 (theoretical paper)")

        # Phase 8: Additional Considerations (always executed)
        logger.info("Phase 8: Additional considerations")
        self.api_call_count += 1
        phase8_result = self.phase8.process(content)

        # Compile results
        assessment_result = VirtualTutorAssessmentResult(
            phase1=phase1_result,
            phase2=phase2_result,
            phase3=phase3_result,
            phase4=phase4_result,
            phase5=phase5_result,
            phase6=phase6_result,
            phase7=phase7_result,
            phase8=phase8_result
        )

        logger.info(f"Assessment complete. Total API calls: {self.api_call_count}")

        # Convert to dictionary for storage
        return self._flatten_assessment(assessment_result)

    def _flatten_assessment(self, result: VirtualTutorAssessmentResult) -> Dict[str, Any]:
        """Flatten the nested assessment result for database storage"""
        flat = {}

        # Phase 1
        flat['is_virtual_tutor'] = result.phase1.is_virtual_tutor
        flat['is_implementation'] = result.phase1.is_implementation

        # Phase 2
        if result.phase2:
            flat['deployment_status'] = result.phase2.deployment_status
            flat['llm_model'] = result.phase2.llm_model
            flat['uses_rag'] = result.phase2.uses_rag
            flat['primary_function'] = result.phase2.primary_function
            flat['subject_domain'] = result.phase2.subject_domain
            flat['generates_assessments'] = result.phase2.generates_assessments

        # Phase 3
        if result.phase3:
            flat['publication_type'] = result.phase3.publication_type
            flat['availability'] = result.phase3.availability

        # Phase 4
        if result.phase4:
            flat['lms_integration'] = result.phase4.lms_integration
            flat['architecture_components'] = ','.join(result.phase4.architecture_components)
            flat['interaction_modality'] = ','.join(result.phase4.interaction_modality)
            flat['analytics_features'] = ','.join(result.phase4.analytics_features)

        # Phase 5
        if result.phase5:
            flat['pedagogical_features'] = ','.join(result.phase5.pedagogical_features)
            flat['personalization'] = result.phase5.personalization
            flat['supports_collaboration'] = result.phase5.supports_collaboration
            if result.phase5.collaboration_types:
                flat['collaboration_types'] = ','.join(result.phase5.collaboration_types)
            else:
                flat['collaboration_types'] = None

        # Phase 6
        if result.phase6:
            flat['empirical_evaluation'] = result.phase6.empirical_evaluation
            if result.phase6.aspects_evaluated:
                flat['aspects_evaluated'] = ','.join(result.phase6.aspects_evaluated)
            else:
                flat['aspects_evaluated'] = None
            flat['sample_size'] = result.phase6.sample_size
            flat['evaluation_duration'] = result.phase6.evaluation_duration

        # Phase 7
        if result.phase7:
            flat['institution_type'] = result.phase7.institution_type
            flat['development_approach'] = result.phase7.development_approach
            flat['language_support'] = result.phase7.language_support

        # Phase 8
        if result.phase8:
            flat['privacy_protection'] = result.phase8.privacy_protection
            flat['cost_requirements'] = result.phase8.cost_requirements
            flat['reference_architecture'] = result.phase8.reference_architecture

        return flat
