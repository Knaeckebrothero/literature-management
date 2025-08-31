"""
Evaluates the content of a paper to determine if it relates to neurosymbolic AI and provides
an assessment if applicable.

This method performs a multi-step analysis using a language model to identify relevance,
classify the paper type, and generate a summary. The method combines results from various
internal assessments to construct a detailed evaluation report.

Parameters:
content: str
    The content of the paper to assess.

Returns:
Optional[Dict[str, Any]]
    A dictionary containing the assessment results with the following keys:
    - 'is_neurosymbolic': Boolean indicating if the paper relates to neurosymbolic AI.
    - 'paper_type': Classification of the paper's type.
    - 'summary': A summary of the paper content.
    None if no valid assessment can be compiled due to errors or empty content.
"""
from assessment.basic import InitialAssessment, TypeAssessment
from assessment.advanced import SummaryAssessment
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from typing import Optional, Dict, Any


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_prompt_template(file_path: str) -> str:
    """
    Loads a prompt template from a file or returns a default template string if the file is not
    found. The function is designed to streamline retrieval of structured template data for specific
    use cases that require formatted prompts.

    Parameters:
    file_path: str
        The path to the file containing the prompt template.

    Returns:
    str
        The content of the file as a string, or a default template string if the file is not
        found.
    """
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return """
        Please analyze the following research paper content and provide a structured assessment.
        
        Paper content:
        {paper_content}
        
        Assessment instructions:
        {format_instructions}
        """

class PaperAssessment:
    """
    Represents an assessment process for research papers related to neurosymbolic AI.

    This class provides functionalities to analyze a given paper's content to determine its
    relevance, classify its type, and generate its summary. It uses a language model (LLM) for
    analysis, structured parsers for interpreting the model's output, and predefined templates
    for generating prompts.

    Attributes
    ----------
    model : Any
        Language model instance used for generating responses during paper assessment.
    prompt_path : str
        Path to the file containing prompt templates used in the assessment process.
    """
    def __init__(self, model, prompt_path):
        self.model = model
        self.prompt_path = prompt_path
        self._setup_parsers()

    def _setup_parsers(self):
        """
        Sets up parsers and prompt templates used for processing paper content. This
        method initializes multiple parsers based on Pydantic models and creates
        corresponding prompt templates with specific format instructions. These parsers
        and templates are used for handling initial, type, and summary assessments.

        Attributes
        ----------
        initial_parser : PydanticOutputParser
            Parser for handling initial assessment structured according to the
            'InitialAssessment' Pydantic model.
        type_parser : PydanticOutputParser
            Parser for handling type assessment structured according to the
            'TypeAssessment' Pydantic model.
        summary_parser : PydanticOutputParser
            Parser for handling summary assessment structured according to the
            'SummaryAssessment' Pydantic model.
        initial_template : PromptTemplate
            Template built for initial assessment using format instructions from
            `initial_parser`.
        type_template : PromptTemplate
            Template built for type assessment using format instructions from
            `type_parser`.
        summary_template : PromptTemplate
            Template built for summary assessment using format instructions from
            `summary_parser`.
        """
        self.initial_parser = PydanticOutputParser(pydantic_object=InitialAssessment)
        self.type_parser = PydanticOutputParser(pydantic_object=TypeAssessment)
        self.summary_parser = PydanticOutputParser(pydantic_object=SummaryAssessment)

        template = _load_prompt_template(self.prompt_path)

        self.initial_template = PromptTemplate(
            template=template,
            input_variables=["paper_content"],
            partial_variables={"format_instructions": self.initial_parser.get_format_instructions()}
        )
        self.type_template = PromptTemplate(
            template=template,
            input_variables=["paper_content"],
            partial_variables={"format_instructions": self.type_parser.get_format_instructions()}
        )
        self.summary_template = PromptTemplate(
            template=template,
            input_variables=["paper_content"],
            partial_variables={"format_instructions": self.summary_parser.get_format_instructions()}
        )

    def _get_llm_response(self, template: PromptTemplate, content: str) -> Optional[str]:
        """
        Processes the interaction with a Language Learning Model (LLM) and retrieves
        the generated response based on a given template and provided content.

        Parameters:
        template: PromptTemplate
            The template used to format the content before invoking the model.
        content: str
            The content to include in the formatted prompt.

        Returns:
        Optional[str]
            The generated response from the LLM, or None if an error occurs or the
            response type is unexpected.

        Raises:
        Exception
            If an error occurs during the model invocation or response handling.
        """
        try:
            prompt = template.format(paper_content=content)
            response = self.model.invoke(prompt)

            # Handle different response types
            if isinstance(response, str):
                return response
            elif isinstance(response, dict) and 'text' in response:
                return response['text']
            elif hasattr(response, 'content'):
                return response.content
            else:
                logger.error(f"Unexpected response type from LLM: {type(response)}")
                return None
        except Exception as e:
            logger.error(f"Error getting LLM response: {str(e)}")
            return None

    def _parse_response(self, response: Optional[str], parser: PydanticOutputParser, default_obj: Any) -> Any:
        """
        Parses a response string using a PydanticOutputParser and returns the resulting
        object, or a default object in case of failure.

        Parameters:
        response (Optional[str]): The response string to be parsed. If None or empty,
                                   the default object is returned.
        parser (PydanticOutputParser): The parser instance used to parse the response
                                        string.
        default_obj (Any): The object returned if the response is None or parsing fails.

        Returns:
        Any: The parsed object if successful; otherwise, the default object.
        """
        if not response:
            return default_obj

        try:
            return parser.parse(response)
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return default_obj

    def _check_viability(self, content: str) -> InitialAssessment:
        """
        Evaluates the initial viability of the provided content using a language model response
        and parses the result to generate an InitialAssessment.

        Parameters:
        content: str
            The input content that needs assessment for viability.

        Returns:
        InitialAssessment
            Parsed assessment result indicating the initial evaluation
            of the content's characteristics.
        """
        response = self._get_llm_response(self.initial_template, content)
        return self._parse_response(
            response,
            self.initial_parser,
            InitialAssessment(is_neurosymbolic=False)
        )

    def _assess_type(self, content: str) -> TypeAssessment:
        """
        Determines the type assessment of the provided content.

        The method utilizes a template-based approach to query a language model
        and subsequently parses the response to assess the type.

        Args:
            content (str): The content whose type is to be assessed.

        Returns:
            TypeAssessment: The resulting assessment of the content's type.
        """
        response = self._get_llm_response(self.type_template, content)
        return self._parse_response(
            response,
            self.type_parser,
            TypeAssessment(paper_type="other")
        )

    def _summarize(self, content: str) -> SummaryAssessment:
        """
        Summarizes the given content using a specified template and parser.

        This method utilizes a language model (LLM) to generate a summary of the provided
        content. It parses the LLM response using a pre-defined parser to extract the summary
        and returns it encapsulated in a `SummaryAssessment` object.

        Parameters:
        content (str): The content to be summarized.

        Returns:
        SummaryAssessment: An object containing the generated paper summary. If the summarization
        fails, the `paper_summary` attribute in the returned `SummaryAssessment` object
        will indicate failure.
        """
        response = self._get_llm_response(self.summary_template, content)
        return self._parse_response(
            response,
            self.summary_parser,
            SummaryAssessment(paper_summary="Summary generation failed")
        )

    def assess_paper(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Evaluates the content of a paper to determine if it relates to neurosymbolic AI and provides
        an assessment if applicable.

        Args:
            content (str): The content of the paper to assess.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the assessment results including
            whether the paper is about neurosymbolic AI, its type, and a summary. Returns
            None if the paper is not about neurosymbolic AI or if an error occurs during
            the assessment.

        Raises:
            Exception: Catches general exceptions during paper assessment and logs errors
            without re-raising them.
        """
        try:
            # Initial assessment
            initial_assessment = self._check_viability(content)
            if not initial_assessment.is_neurosymbolic:
                logger.info("Paper is not primarily about neurosymbolic AI")
                return None

            # Full assessment
            logger.info("Paper is about neurosymbolic AI, proceeding with full assessment")
            type_assessment = self._assess_type(content)
            summary_assessment = self._summarize(content)

            return {
                "is_neurosymbolic": initial_assessment.is_neurosymbolic,
                "paper_type": type_assessment.paper_type,
                "summary": summary_assessment.paper_summary
            }

        except Exception as e:
            logger.error(f"Error in paper assessment: {str(e)}")
            return None
