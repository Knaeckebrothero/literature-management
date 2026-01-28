from pydantic import BaseModel, Field
from typing import Literal


class InitialAssessment(BaseModel):
    is_neurosymbolic: bool = Field(
        description="Whether the paper is primarily about virtual tutors using large language models (LLMs). This is the case if at least one fourth of the paper's total content deals with or focuses on AI-based educational agents, chatbots, or virtual teaching assistants that leverage LLMs or similar language technologies to support learning in higher education contexts. Key indicators include substantial discussion of: LLM-based tutoring systems, educational dialogue agents, automated question answering for academic subjects, personalized learning via AI tutors, integration of language models with educational platforms, retrieval-augmented generation for educational content, implementation of virtual teaching assistants, or empirical studies measuring learning outcomes from LLM-based tutoring. Papers that only briefly mention AI in education or language models without significant elaboration on their application to tutoring should not be considered primarily about the topic."
    )


class TypeAssessment(BaseModel):
    paper_type: Literal[
        "survey",           # Comprehensive literature reviews, systematic reviews, or meta-analyses
        "methodology",      # Papers proposing new methods, algorithms, or frameworks
        "architecture",     # Papers introducing novel neural-symbolic architectures or system designs
        "application",      # Papers applying existing NeySy approaches to specific domains/problems
        "theoretical",      # Papers focused on theoretical foundations or formal analysis
        "position",         # Position papers, viewpoints, or perspective articles
        "book_chapter",     # Book chapters or excerpts from longer works
        "workshop",         # Workshop papers or extended abstracts
        "tool",             # Papers presenting software tools or implementations
        "other"             # Papers that don't fit the above categories
    ] = Field(
        description="""Determine the primary category of the paper based on its main contribution and content type. Choose the most specific applicable category:
            - 'survey': For papers that primarily review, synthesize, or analyze existing literature. This includes systematic reviews, meta-analyses, and comprehensive literature surveys that map the field without introducing new methods.
            - 'methodology': For papers that introduce new methods, algorithms, approaches, or techniques for neural-symbolic integration. The contribution should be a novel way of combining neural and symbolic components.
            - 'architecture': For papers that propose new system architectures or structural designs for neural-symbolic systems. This includes novel frameworks for integrating neural networks with symbolic reasoning components.
            - 'application': For papers that primarily focus on applying existing neural-symbolic methods to specific domains or problems. The main contribution should be the novel application or adaptation rather than the method itself.
            - 'theoretical': For papers that develop theoretical foundations, provide formal analyses, or explore fundamental properties of neural-symbolic systems. This includes papers focusing on mathematical frameworks or theoretical capabilities.
            - 'position': For papers that present viewpoints, perspectives, or arguments about the direction of neural-symbolic AI without necessarily introducing new methods or presenting experimental results.
            - 'book_chapter': For content that is part of a larger work, typically providing broader coverage or educational material about neural-symbolic approaches.
            - 'workshop': For shorter papers, extended abstracts, or work-in-progress reports typically presented at workshops or symposia.
            - 'tool': For papers that primarily present software implementations, frameworks, or tools for neural-symbolic integration.
            - 'other': For papers that don't clearly fit into any of the above categories but are still relevant to neural-symbolic AI.
        
            Select the category that best matches the paper's primary contribution and format. If a paper could fit multiple categories, choose the one that represents its main contribution.
            """
    )
