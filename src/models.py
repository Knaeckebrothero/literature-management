"""
Pydantic models for SLR project configuration and content matrix.

Defines the structure for project questions, answer types, and assessment results.
"""
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class AnswerType(str, Enum):
    """Supported answer types for content matrix questions."""
    BOOLEAN = "boolean"
    ENUM = "enum"
    TEXT = "text"
    NUMERIC = "numeric"


class Question(BaseModel):
    """A question in the content matrix configuration."""

    key: str = Field(
        description="Unique identifier for this question (used as column key)",
        min_length=1,
        max_length=64,
        pattern=r'^[a-z][a-z0-9_]*$'
    )
    text: str = Field(
        description="The question text shown to the agent",
        min_length=1
    )
    answer_type: AnswerType = Field(
        description="Type of answer expected"
    )
    options: Optional[list[str]] = Field(
        default=None,
        description="Valid options for enum-type questions"
    )
    description: Optional[str] = Field(
        default=None,
        description="Additional context or instructions for the agent"
    )

    @field_validator('options')
    @classmethod
    def validate_options(cls, v, info):
        """Ensure enum questions have options defined."""
        if info.data.get('answer_type') == AnswerType.ENUM:
            if not v or len(v) < 2:
                raise ValueError("Enum questions must have at least 2 options")
        return v

    def format_for_agent(self) -> str:
        """Format the question for the agent prompt."""
        prompt = f"Question: {self.text}\n"
        prompt += f"Answer type: {self.answer_type.value}\n"

        if self.description:
            prompt += f"Instructions: {self.description}\n"

        if self.answer_type == AnswerType.BOOLEAN:
            prompt += "Respond with: yes or no\n"
        elif self.answer_type == AnswerType.ENUM:
            prompt += f"Respond with one of: {', '.join(self.options)}\n"
        elif self.answer_type == AnswerType.NUMERIC:
            prompt += "Respond with a number (or 'N/A' if not applicable)\n"
        elif self.answer_type == AnswerType.TEXT:
            prompt += "Provide a concise text answer (1-3 sentences)\n"

        return prompt


class ProjectConfig(BaseModel):
    """Configuration for an SLR project's content matrix."""

    questions: list[Question] = Field(
        default_factory=list,
        description="List of questions to assess for each source"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional custom system prompt for the agent"
    )
    model: Optional[str] = Field(
        default=None,
        description="LLM model to use (defaults to CITATION_LLM_MODEL env var)"
    )

    @field_validator('questions')
    @classmethod
    def validate_unique_keys(cls, v):
        """Ensure all question keys are unique."""
        keys = [q.key for q in v]
        if len(keys) != len(set(keys)):
            raise ValueError("Question keys must be unique")
        return v

    def get_question(self, key: str) -> Optional[Question]:
        """Get a question by its key."""
        for q in self.questions:
            if q.key == key:
                return q
        return None

    def question_keys(self) -> list[str]:
        """Get list of all question keys."""
        return [q.key for q in self.questions]


class Confidence(str, Enum):
    """Confidence level for an answer."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Citation(BaseModel):
    """A citation reference within an answer."""

    quote: str = Field(description="The quoted or paraphrased text")
    page: Optional[int] = Field(default=None, description="Page number if applicable")
    section: Optional[str] = Field(default=None, description="Section identifier")


class Answer(BaseModel):
    """An answer to a content matrix question."""

    question_key: str = Field(description="Key of the question being answered")
    value: Any = Field(description="The answer value (type depends on question)")
    confidence: Confidence = Field(
        default=Confidence.MEDIUM,
        description="Agent's confidence in this answer"
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Brief explanation of how the answer was derived"
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Citations supporting this answer"
    )

    def to_db_dict(self, project_id: int, source_id: int) -> dict:
        """Convert to dictionary for database insertion."""
        import json
        return {
            'project_id': project_id,
            'source_id': source_id,
            'question_key': self.question_key,
            'answer': str(self.value) if self.value is not None else None,
            'confidence': self.confidence.value,
            'citations': json.dumps([c.model_dump() for c in self.citations])
        }


class AssessmentResult(BaseModel):
    """Result of assessing a single source against all questions."""

    source_id: int
    answers: list[Answer] = Field(default_factory=list)
    error: Optional[str] = Field(default=None, description="Error message if assessment failed")

    @property
    def is_complete(self) -> bool:
        """Check if all questions were answered without error."""
        return self.error is None and len(self.answers) > 0


# Example config for reference
EXAMPLE_CONFIG = ProjectConfig(
    questions=[
        Question(
            key="uses_llm",
            text="Does the system use a large language model?",
            answer_type=AnswerType.BOOLEAN,
            description="Look for mentions of GPT, BERT, LLaMA, or similar models"
        ),
        Question(
            key="evaluation_method",
            text="What evaluation methodology was used?",
            answer_type=AnswerType.ENUM,
            options=["controlled_experiment", "survey", "case_study", "technical_evaluation", "none"]
        ),
        Question(
            key="sample_size",
            text="What was the sample size of the evaluation?",
            answer_type=AnswerType.NUMERIC,
            description="Number of participants or data points in the evaluation"
        ),
        Question(
            key="main_contribution",
            text="What is the main contribution of this paper?",
            answer_type=AnswerType.TEXT
        ),
    ]
)
