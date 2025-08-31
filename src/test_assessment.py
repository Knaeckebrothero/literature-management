"""
This module provides functionality for testing the virtual tutor assessment system, utilizing
samples of academic papers to evaluate their content. The module includes a function to
initialize necessary settings, load environment variables, and test the assessment system to
determine whether the paper pertains to a virtual tutor system.

The primary components and dependencies include OpenAI language models, an assessment framework,
and logging utilities to track the test process.

Modules:
- dotenv: To manage environment variables.
- langchain_openai: To initialize and configure an OpenAI model.
- assessment.virtual_tutor_assessment: To perform the assessment of the given papers.

Logging: This module uses Python’s built-in logging library to output progress and results.

Environment Variables:
Environmental configurations are loaded at runtime using dotenv to support external API
integration.
"""
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from assessment.virtual_tutor_assessment import VirtualTutorAssessment


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample test content
SAMPLE_VIRTUAL_TUTOR_PAPER = """
Title: An Intelligent Virtual Tutor System for Computer Science Education Using GPT-4

Abstract:
This paper presents the design and implementation of an intelligent virtual tutor system 
that leverages GPT-4 to provide personalized learning support for undergraduate computer 
science students. The system integrates with Moodle and uses retrieval-augmented generation 
(RAG) to access course materials and provide context-aware responses to student queries.

Introduction:
Virtual tutors based on large language models (LLMs) have shown great promise in higher 
education settings. Our system specifically targets introductory programming courses and 
provides features such as code explanation, debugging assistance, and personalized feedback 
on programming assignments.

System Architecture:
The virtual tutor is built using a microservices architecture with the following components:
- GPT-4 API for natural language processing
- Vector database (Pinecone) for course content retrieval
- Moodle integration via REST API
- Real-time analytics dashboard for instructors

Evaluation:
We conducted a controlled experiment with 150 students over one semester. Students were 
randomly assigned to either use the virtual tutor or traditional teaching assistant support. 
Results showed significant improvements in learning outcomes and student engagement.

Conclusion:
The virtual tutor system demonstrates the potential of LLM-based educational technology 
in higher education settings.
"""

SAMPLE_NON_VIRTUAL_TUTOR_PAPER = """
Title: Deep Learning Approaches for Image Classification

Abstract:
This paper surveys recent advances in deep learning techniques for image classification tasks.
We review various convolutional neural network architectures and their performance on 
standard benchmarks.

Introduction:
Image classification has been revolutionized by deep learning methods. This survey examines
the evolution of CNN architectures from AlexNet to modern transformer-based approaches.

Methods:
We analyze different architectural innovations including residual connections, attention
mechanisms, and neural architecture search.

Conclusion:
Deep learning continues to push the boundaries of image classification performance.
"""


def test_assessment_system():
    """
    Tests the functionality of the Virtual Tutor Assessment system using two sample papers:
    one related to virtual tutors and one not.

    The function performs the following steps:
    1. Loads environment variables required for initializing the model.
    2. Creates a language learning model (LLM) instance based on the specified
       model configuration.
    3. Initializes the Virtual Tutor Assessment system using the LLM.
    4. Assesses a sample virtual tutor-related paper, verifying the results and
       outputting key assessment details, alongside the full results.
    5. Assesses a non-virtual tutor paper to ensure it is correctly identified
       as irrelevant to virtual tutors.
    6. Logs outcomes and summarizes the testing process.

    Parameters: None

    Raises:
        Any raised errors are not explicitly handled in this function.

    Return:
        This function does not return a value.
    """

    # Load environment variables
    load_dotenv()

    # Initialize model
    logger.info("Initializing LLM...")
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        seed=42
    )

    # Initialize assessment system
    logger.info("Initializing assessment system...")
    assessment = VirtualTutorAssessment(model=llm)

    # Test 1: Virtual Tutor Paper
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Virtual Tutor Paper")
    logger.info("="*50)

    result1 = assessment.assess_paper(SAMPLE_VIRTUAL_TUTOR_PAPER)

    if result1:
        logger.info("Assessment completed successfully!")
        logger.info(f"Total API calls: {assessment.api_call_count}")

        # Display key results
        logger.info("\nKey Results:")
        logger.info(f"- Is Virtual Tutor: {result1.get('is_virtual_tutor')}")
        logger.info(f"- Is Implementation: {result1.get('is_implementation')}")
        logger.info(f"- LLM Model: {result1.get('llm_model')}")
        logger.info(f"- Primary Function: {result1.get('primary_function')}")
        logger.info(f"- Uses RAG: {result1.get('uses_rag')}")
        logger.info(f"- Evaluation Type: {result1.get('empirical_evaluation')}")

        # Display all results
        logger.info("\nFull Assessment:")
        for key, value in result1.items():
            if value is not None:
                logger.info(f"  {key}: {value}")
    else:
        logger.error("Assessment returned None - paper not identified as virtual tutor")

    # Test 2: Non-Virtual Tutor Paper
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Non-Virtual Tutor Paper")
    logger.info("="*50)

    result2 = assessment.assess_paper(SAMPLE_NON_VIRTUAL_TUTOR_PAPER)

    if result2:
        logger.error("ERROR: Non-virtual tutor paper was incorrectly assessed")
        logger.info(f"Results: {result2}")
    else:
        logger.info("SUCCESS: Paper correctly identified as not about virtual tutors")
        logger.info(f"Total API calls: {assessment.api_call_count}")

    logger.info("\n" + "="*50)
    logger.info("Testing complete!")


if __name__ == "__main__":
    test_assessment_system()
