"""
Base class for phase processors
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from typing import Optional, Dict, Any

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
Please analyze the following research paper content and answer the questions below.

Paper content:
{content}

Questions to answer:
{questions}

{format_instructions}
"""
