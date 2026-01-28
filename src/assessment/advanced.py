"""
A comprehensive model for structuring a detailed assessment of a research paper related to virtual tutors using large language models (LLMs).

This class models the structure for creating a well-defined assessment of academic papers in the context
of virtual tutoring systems in higher education. The assessment integrates aspects such as context, contribution,
implementation, results, and implications. It aims to produce an evaluative summary that is concise yet rich
in specific, actionable insights for advancing the research and use of LLM-based virtual tutors.
"""
from pydantic import BaseModel, Field


class SummaryAssessment(BaseModel):
    paper_summary: str = Field(
        description="""Provide a comprehensive yet concise assessment (5-7 sentences total) of the paper focusing on its relevance to virtual tutors using large language models (LLMs) in higher education. The assessment should integrate the paper's summary and key takeaways in a structured format:

        1. CONTEXT: Briefly state the educational challenge or opportunity that the paper addresses through LLM-based tutoring systems.
        
        2. CONTRIBUTION: Clearly describe what the paper contributes to the field, being specific about:
           - Novel methods, architectures, or approaches to virtual tutoring
           - Integration techniques for LLMs in educational contexts
           - Specific learning tasks or domains supported by the virtual tutor
        
        3. IMPLEMENTATION: Outline the technical implementation, including:
           - Which language models or AI technologies were utilized (e.g., BERT, GPT, LLaMA, T5)
           - How the system integrates with learning management systems or educational platforms
           - Key architectural components (e.g., retrieval-augmented generation, knowledge graphs)
        
        4. RESULTS: Summarize the most significant empirical findings:
           - Quantitative learning outcomes or improvements demonstrated
           - User engagement metrics or satisfaction data
           - Comparative advantages over traditional tutoring or other AI approaches
        
        5. IMPLICATIONS: Highlight the practical significance for higher education:
           - How this work advances virtual tutoring in educational settings
           - Notable limitations or challenges identified
           - Future research directions suggested

        For surveys or review papers, focus on the scope of the review and its key insights about the state of virtual tutors rather than specific technical implementations.
        
        Write in clear, academic language and prioritize specific, concrete details over general statements. Emphasize actionable insights and significant contributions that would be valuable for understanding the evolution and current state of virtual tutors using LLMs.
        
        Example format:
        "This paper addresses [specific educational challenge] by developing a virtual tutor that [main approach/contribution]. The system implements [specific technical details] based on [LLM type/architecture]. The authors demonstrate [specific results/findings], suggesting that [implications for educational practice or research]. Notable limitations include [challenges] which point to future work in [research direction]."
        """,
        default="Assessment not available"
    )
