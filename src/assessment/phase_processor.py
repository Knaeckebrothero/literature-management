"""
This module defines the abstract base class and logic for processing different phases
of a systematic literature review using a language model. It includes methods for
building questions, generating prompts, and processing responses.

Classes:
- PhaseProcessor: An abstract base class for processing phases of a systematic
  literature review, defining methods for question building, content processing,
  and retrieving default responses.

Constants:
- PHASE_PROMPT_TEMPLATE: A string template used to construct prompts for processing
  phase questions.
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging

logger = logging.getLogger(__name__)


class PhaseProcessor(ABC):
    """Base class for all phase processors"""

    def __init__(self, model, prompt_template: str):
        self.model = model
        self.prompt_template = prompt_template
        self.parser = PydanticOutputParser(pydantic_object=self.get_phase_model())

    @abstractmethod
    def get_phase_model(self) -> type[BaseModel]:
        """Return the Pydantic model for this phase"""
        pass

    @abstractmethod
    def build_questions(self, **conditions) -> str:
        """Build the questions for this phase based on conditions"""
        pass

    def process(self, content: str, **conditions) -> BaseModel:
        """Process the content and return structured results"""
        try:
            # Build the questions based on conditions
            questions = self.build_questions(**conditions)

            # Create the prompt
            template = PromptTemplate(
                template=self.prompt_template,
                input_variables=["content", "questions", "format_instructions"]
            )

            prompt = template.format(
                content=content,
                questions=questions,
                format_instructions=self.parser.get_format_instructions()
            )

            # Get response from LLM
            response = self.model.invoke(prompt)

            # Handle different response types
            if isinstance(response, str):
                response_text = response
            elif hasattr(response, 'content'):
                response_text = response.content
            else:
                logger.error(f"Unexpected response type: {type(response)}")
                return self.get_default_response()

            # Parse the response
            return self.parser.parse(response_text)

        except Exception as e:
            logger.error(f"Error in phase processing: {str(e)}")
            return self.get_default_response()

    @abstractmethod
    def get_default_response(self) -> BaseModel:
        """Return a default response for error cases"""
        pass


# Simple prompt template that will be used for all phases
PHASE_PROMPT_TEMPLATE = """
You are an expert reviewer conducting a systematic literature review on virtual intelligent tutors in higher education, with a focus on systems using large language models (LLMs).

Your task is to carefully analyze the provided research paper and answer specific assessment questions.

IMPORTANT GUIDELINES:
1. Base your answers ONLY on information explicitly stated in the paper. Do not make assumptions or infer beyond what is written.
2. Look for evidence throughout the entire paper - implementation details often appear in methodology sections, appendices, or system descriptions.
3. If information for a question is not found, select "not_specified" rather than guessing.
4. Pay attention to subtle distinctions (e.g., "planned" vs "implemented", "proposed" vs "deployed").
5. For multi-select questions, be comprehensive - identify ALL applicable options.
6. Consider the paper's main focus, not just passing mentions, when answering classification questions.

CONTEXT:
This assessment is part of a systematic review examining:
- Virtual tutors/chatbots/AI assistants specifically designed for higher education
- Systems using NLP/LLMs for educational support
- Both theoretical discussions and practical implementations
- Technical architectures, pedagogical features, and empirical evaluations

Paper content:
{content}

Questions to answer:
{questions}

{format_instructions}

Remember: When uncertain, choose "not_specified" rather than making assumptions. The goal is accurate data extraction, not interpretation.
"""
