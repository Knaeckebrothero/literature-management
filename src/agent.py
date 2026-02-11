"""
Assessment Agent for SLR Content Matrix.

Uses a reasoning model to analyze source content and answer configured questions.
Supports optional citation engine integration for verified citations.
"""
import json
import logging
import os
from typing import Any, Optional

from pydantic import BaseModel, Field

from models import Answer, AnswerType, Citation, Confidence, Question


logger = logging.getLogger(__name__)


class AgentResponse(BaseModel):
    """Structured response from the agent for a single question."""

    answer: Any = Field(description="The answer value")
    confidence: str = Field(description="Confidence level: high, medium, or low")
    reasoning: str = Field(description="Brief explanation of the answer")
    quotes: list[str] = Field(
        default_factory=list,
        description="Relevant quotes from the source supporting this answer"
    )


class AssessmentAgent:
    """
    Agent for assessing sources against content matrix questions.

    Uses OpenAI API with structured outputs to analyze source content
    and generate answers in the expected format.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the assessment agent.

        Args:
            model: LLM model name (defaults to CITATION_LLM_MODEL env var or gpt-4o-mini)
            system_prompt: Optional custom system prompt
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Optional custom API endpoint (for OpenAI-compatible providers)
        """
        self.model = model or os.getenv('CITATION_LLM_MODEL', 'gpt-4o-mini')
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('CITATION_LLM_URL')

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.system_prompt = system_prompt or self._default_system_prompt()
        self._client = None

    def _default_system_prompt(self) -> str:
        """Default system prompt for assessment."""
        return """You are a research assistant analyzing academic papers for a systematic literature review.

Your task is to carefully read the provided source content and answer questions about it.
Be precise and evidence-based. Only answer based on what's explicitly stated or clearly implied in the text.

For each question:
1. Search the content for relevant information
2. Formulate your answer based on the evidence found
3. Note your confidence level (high if explicitly stated, medium if implied, low if uncertain)
4. Include relevant quotes that support your answer

If the source doesn't contain information to answer a question, say so clearly.
Do not make assumptions or invent information not present in the source."""

    @property
    def client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "openai package is required. Install with: pip install openai"
                )

            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url

            self._client = OpenAI(**kwargs)

        return self._client

    def assess_question(
        self,
        source_content: str,
        question: Question,
        source_title: Optional[str] = None,
    ) -> Answer:
        """
        Assess a single question against source content.

        Args:
            source_content: The text content of the source (abstract, full text, etc.)
            question: The question to answer
            source_title: Optional title for context

        Returns:
            Answer object with the agent's response
        """
        logger.info(f"Assessing question '{question.key}' for source: {source_title or 'unknown'}")

        # Build the prompt
        prompt = self._build_prompt(source_content, question, source_title)

        try:
            # Call the LLM
            response = self._call_llm(prompt, question)

            # Parse and validate the response
            answer = self._parse_response(response, question)
            logger.debug(f"Answer for '{question.key}': {answer.value} (confidence: {answer.confidence})")

            return answer

        except Exception as e:
            logger.error(f"Error assessing question '{question.key}': {e}")
            # Return a low-confidence answer indicating the error
            return Answer(
                question_key=question.key,
                value=None,
                confidence=Confidence.LOW,
                reasoning=f"Assessment failed: {str(e)}",
                citations=[]
            )

    def _build_prompt(
        self,
        source_content: str,
        question: Question,
        source_title: Optional[str] = None,
    ) -> str:
        """Build the user prompt for the LLM."""
        parts = []

        if source_title:
            parts.append(f"# Source: {source_title}\n")

        parts.append("## Content\n")
        # Truncate very long content to fit context window
        max_content_len = 12000
        if len(source_content) > max_content_len:
            parts.append(source_content[:max_content_len])
            parts.append("\n\n[Content truncated due to length...]\n")
        else:
            parts.append(source_content)

        parts.append("\n\n## Question\n")
        parts.append(question.format_for_agent())

        parts.append("\n## Response Format\n")
        parts.append("Respond with a JSON object containing:\n")
        parts.append("- answer: your answer (matching the expected type)\n")
        parts.append("- confidence: 'high', 'medium', or 'low'\n")
        parts.append("- reasoning: brief explanation (1-2 sentences)\n")
        parts.append("- quotes: list of relevant quotes from the source (up to 3)\n")

        return "".join(parts)

    def _call_llm(self, prompt: str, question: Question) -> dict:
        """Call the LLM and return the parsed response."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Use response_format for JSON mode
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=1000,
        )

        content = response.choices[0].message.content
        return json.loads(content)

    def _parse_response(self, response: dict, question: Question) -> Answer:
        """Parse and validate the LLM response into an Answer."""
        raw_answer = response.get('answer')

        # Coerce answer to expected type
        value = self._coerce_answer(raw_answer, question)

        # Parse confidence
        confidence_str = response.get('confidence', 'medium').lower()
        try:
            confidence = Confidence(confidence_str)
        except ValueError:
            confidence = Confidence.MEDIUM

        # Parse citations from quotes
        citations = []
        for quote in response.get('quotes', []):
            if quote and isinstance(quote, str):
                citations.append(Citation(quote=quote.strip()))

        return Answer(
            question_key=question.key,
            value=value,
            confidence=confidence,
            reasoning=response.get('reasoning', ''),
            citations=citations
        )

    def _coerce_answer(self, raw: Any, question: Question) -> Any:
        """Coerce the raw answer to the expected type."""
        if raw is None:
            return None

        if question.answer_type == AnswerType.BOOLEAN:
            if isinstance(raw, bool):
                return raw
            if isinstance(raw, str):
                lower = raw.lower().strip()
                if lower in ('yes', 'true', '1'):
                    return True
                if lower in ('no', 'false', '0'):
                    return False
            return None

        elif question.answer_type == AnswerType.ENUM:
            if isinstance(raw, str) and question.options:
                # Try exact match first
                if raw in question.options:
                    return raw
                # Try case-insensitive match
                lower = raw.lower()
                for opt in question.options:
                    if opt.lower() == lower:
                        return opt
            return None

        elif question.answer_type == AnswerType.NUMERIC:
            if isinstance(raw, (int, float)):
                return raw
            if isinstance(raw, str):
                raw = raw.strip()
                if raw.lower() in ('n/a', 'na', 'none', 'not available'):
                    return None
                try:
                    return float(raw) if '.' in raw else int(raw)
                except ValueError:
                    return None
            return None

        elif question.answer_type == AnswerType.TEXT:
            if raw:
                return str(raw).strip()
            return None

        return raw


def create_agent(
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> AssessmentAgent:
    """
    Factory function to create an assessment agent.

    Args:
        model: LLM model name (defaults to env var)
        system_prompt: Custom system prompt

    Returns:
        Configured AssessmentAgent instance
    """
    return AssessmentAgent(model=model, system_prompt=system_prompt)
