"""
This module contains functions for interacting with an SQLite database to
retrieve, filter, and display details about academic papers, along with
their assessment data across various evaluation phases.

The module integrates filtering, normalization of list fields, and visualization
capabilities, making it suitable for exploring and assessing attributes of
papers related to virtual tutors, AI systems, and collaborative learning in
higher education.

"""
import streamlit as st
import pandas as pd
import sqlite3
import base64
from pathlib import Path


def get_connection():
    """
    Establishes and returns a connection to the SQLite database.

    This function creates a connection instance for accessing the SQLite
    database named 'literature.db'. The connection is configured with
    check_same_thread set to False, enabling shared access across threads.

    Returns:
        sqlite3.Connection: The connection object for interacting with
        the SQLite database.
    """
    return sqlite3.connect('literature.db', check_same_thread=False)


def load_paper_details():
    """
    Load paper details and assessments into a DataFrame.

    This function retrieves information about academic papers, including their metadata
    and associated virtual tutor assessments, from a database. It performs a base query
    to gather core information and then enriches the resulting DataFrame with additional
    list fields, such as architecture components or interaction modalities, by joining
    data from related tables.

    Function execution ensures the data is consolidated and returned in a structured format
    suitable for analysis or further processing. The function also guarantees ordered results
    based on assessment date and publication year.

    Args:
        None

    Returns:
        pandas.DataFrame: A DataFrame containing consolidated information about papers with
        additional assessment details, if available.
    """
    conn = get_connection()

    # Base query without list fields
    query = """
            SELECT
                p.id,
                p.doi,
                p.title,
                p.authors,
                p.publication_year,
                p.venue,
                p.volume,
                p.publication_type,
                p.publication_source,
                p.processed,
                p.file_path,
                -- Phase 1
                a.is_virtual_tutor,
                a.is_implementation,
                -- Phase 2
                a.deployment_status,
                a.llm_model,
                a.uses_rag,
                a.primary_function,
                a.subject_domain,
                a.generates_assessments,
                -- Phase 3
                a.publication_type as assessment_publication_type,
                a.availability,
                -- Phase 4 (removing list fields)
                a.lms_integration,
                -- Phase 5 (removing list fields)
                a.personalization,
                a.supports_collaboration,
                -- Phase 6 (removing list fields)
                a.empirical_evaluation,
                a.sample_size,
                a.evaluation_duration,
                -- Phase 7
                a.institution_type,
                a.development_approach,
                a.language_support,
                -- Phase 8
                a.privacy_protection,
                a.cost_requirements,
                a.reference_architecture,
                -- Metadata
                a.assessment_date,
                CASE
                    WHEN a.paper_id IS NULL THEN 'Unassessed'
                    WHEN a.is_virtual_tutor = 1 THEN 'Virtual Tutor'
                    ELSE 'Not Virtual Tutor'
                    END as assessment_status
            FROM papers p
                     LEFT JOIN virtual_tutor_assessments a ON p.id = a.paper_id
            ORDER BY a.assessment_date DESC, p.publication_year DESC
            """

    papers_df = pd.read_sql_query(query, conn)

    if papers_df.empty:
        return papers_df

    # Add list fields
    list_queries = {
        'architecture_components': """
                                   SELECT paper_id, GROUP_CONCAT(component, ',') as architecture_components
                                   FROM assessment_architecture_components
                                   GROUP BY paper_id
                                   """,
        'interaction_modality': """
                                SELECT paper_id, GROUP_CONCAT(modality, ',') as interaction_modality
                                FROM assessment_interaction_modalities
                                GROUP BY paper_id
                                """,
        'analytics_features': """
                              SELECT paper_id, GROUP_CONCAT(feature, ',') as analytics_features
                              FROM assessment_analytics_features
                              GROUP BY paper_id
                              """,
        'pedagogical_features': """
                                SELECT paper_id, GROUP_CONCAT(feature, ',') as pedagogical_features
                                FROM assessment_pedagogical_features
                                GROUP BY paper_id
                                """,
        'collaboration_types': """
                               SELECT paper_id, GROUP_CONCAT(collaboration_type, ',') as collaboration_types
                               FROM assessment_collaboration_types
                               GROUP BY paper_id
                               """,
        'aspects_evaluated': """
                             SELECT paper_id, GROUP_CONCAT(aspect, ',') as aspects_evaluated
                             FROM assessment_aspects_evaluated
                             GROUP BY paper_id
                             """
    }

    # Join each list field
    for field, query in list_queries.items():
        list_df = pd.read_sql_query(query, conn)
        if not list_df.empty:
            papers_df = papers_df.merge(
                list_df,
                left_on='id',
                right_on='paper_id',
                how='left'
            )
            if 'paper_id' in papers_df.columns and 'id' in papers_df.columns:
                papers_df = papers_df.drop('paper_id', axis=1)

    return papers_df


def apply_filters(df, filters):
    """
    Filters the provided DataFrame based on the specified filter criteria.

    This function offers the capability to filter rows in the input DataFrame using various
    criteria provided in the `filters` dictionary. Each filter (e.g., years, LLM model, focus,
    evaluation) selectively filters the data based on its specific condition, refining the
    DataFrame to only include rows matching the given filter values.

    Parameters:
    df: pandas.DataFrame
        The DataFrame to be filtered. Expected to have columns such as `publication_year`,
        `llm_model`, `assessment_status`, `is_implementation`, and `empirical_evaluation`.
    filters: dict
        Dictionary containing the filter criteria. May contain the following keys:
        - 'years' (list of int): Filters rows where the `publication_year` is in the list.
        - 'llm_model' (str): Filters rows by the specified LLM model. Excludes "All".
        - 'focus' (str): Filters rows based on the assessment status and implementation.
          Acceptable values: "Virtual Tutor", "Implementation", "Unassessed/Other".
        - 'evaluation' (str): Filters rows based on the empirical evaluation category.
          Acceptable values: "Evaluated", "Other".

    Returns:
    pandas.DataFrame
        A filtered DataFrame containing rows satisfying the specified filtering criteria.
    """
    filtered_df = df.copy()

    # Handle year filter
    if filters.get('years'):
        filtered_df = filtered_df[filtered_df['publication_year'].isin(filters['years'])]

    # Handle LLM model filter
    if filters.get('llm_model') and filters['llm_model'] != "All":
        filtered_df = filtered_df[
            filtered_df['llm_model'] == filters['llm_model']
            ]

    # Handle focus filter
    if filters.get('focus') and filters['focus'] != "All":
        if filters['focus'] == "Virtual Tutor":
            filtered_df = filtered_df[filtered_df['assessment_status'] == 'Virtual Tutor']
        elif filters['focus'] == "Implementation":
            filtered_df = filtered_df[
                (filtered_df['assessment_status'] == 'Virtual Tutor') &
                (filtered_df['is_implementation'] == True)
                ]
        else:  # "Unassessed/Other"
            filtered_df = filtered_df[filtered_df['assessment_status'].isin(['Unassessed', 'Not Virtual Tutor'])]

    # Handle evaluation filter
    if filters.get('evaluation') and filters['evaluation'] != "All":
        if filters['evaluation'] == "Evaluated":
            filtered_df = filtered_df[
                filtered_df['empirical_evaluation'].isin(['controlled_experiment', 'pilot_study', 'survey_only'])
            ]
        else:
            filtered_df = filtered_df[
                (filtered_df['empirical_evaluation'].isin(['no_evaluation', 'not_specified'])) |
                (filtered_df['empirical_evaluation'].isna())
                ]

    return filtered_df


def display_paper_details(paper, papers_dir: str = "papers"):
    """
    Displays detailed information about a paper within an interactive Streamlit application interface.

    This function extracts and organizes data from a given paper and displays specific details
    categorized into multiple phases, such as general details, core information, system characteristics,
    technical architecture, pedagogical features, evaluation, implementation context, and additional
    information. With conditional rendering, it adjusts the content based on the availability of certain
    attributes. Additionally, the function allows downloading the associated PDF file and optionally
    previewing it within the application.

    Parameters:
        paper (dict): A dictionary containing the metadata and attributes of the paper.
        papers_dir (str, optional): The directory where paper PDFs are stored. Default value: "papers".

    Raises:
        Warning notifications in the Streamlit UI if certain paper assessments or data are unavailable.

    Returns:
        None
    """
    st.header("Paper Details")

    # Basic paper information
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### {paper['title']}")
        st.markdown(f"**Authors:** {paper['authors']}")
        st.markdown(f"**Venue:** {paper['venue']}")
        if pd.notna(paper['volume']):
            st.markdown(f"**Volume:** {paper['volume']}")

    with col2:
        st.markdown(f"**Year:** {paper['publication_year']}")
        st.markdown(f"**DOI:** {paper['doi']}")
        st.markdown(f"**Type:** {paper['publication_type']}")
        st.markdown(f"**Source:** {paper['publication_source']}")

    # Phase 1: Initial Assessment
    st.header("Assessment Results")

    if pd.isna(paper['is_virtual_tutor']):
        st.warning("This paper has not been assessed yet.")
        return

    # Phase 1 & 2: Core Information
    st.subheader("Core Information")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Virtual Tutor",
            "Yes" if paper['is_virtual_tutor'] else "No",
            help="Whether the paper is about virtual tutors in higher education"
        )
    with col2:
        st.metric(
            "Implementation",
            "Yes" if paper['is_implementation'] else "No",
            help="Whether the paper describes an actual implementation"
        )
    with col3:
        if pd.notna(paper['deployment_status']):
            st.metric(
                "Deployment Status",
                paper['deployment_status'].replace('_', ' ').title()
            )

    # Phase 2: System Characteristics
    st.subheader("System Characteristics")
    col1, col2 = st.columns(2)

    with col1:
        if pd.notna(paper['llm_model']):
            st.markdown(f"**LLM Model:** {paper['llm_model'].replace('_', ' ').upper()}")
        if pd.notna(paper['uses_rag']):
            st.markdown(f"**Uses RAG:** {paper['uses_rag'].capitalize()}")
        if pd.notna(paper['primary_function']):
            st.markdown(f"**Primary Function:** {paper['primary_function'].replace('_', ' ').title()}")

    with col2:
        if pd.notna(paper['subject_domain']):
            st.markdown(f"**Subject Domain:** {paper['subject_domain'].replace('_', ' ').title()}")
        if pd.notna(paper['generates_assessments']):
            st.markdown(f"**Generates Assessments:** {paper['generates_assessments'].capitalize()}")

    # Phase 4: Technical Architecture (if applicable)
    if paper['is_implementation'] and pd.notna(paper['lms_integration']):
        st.subheader("Technical Architecture")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**LMS Integration:** {paper['lms_integration'].replace('_', ' ').title()}")
            if pd.notna(paper['architecture_components']):
                components = paper['architecture_components'].split(',')
                st.markdown("**Architecture Components:**")
                for comp in components:
                    st.markdown(f"- {comp.replace('_', ' ').title()}")

        with col2:
            if pd.notna(paper['interaction_modality']):
                modalities = paper['interaction_modality'].split(',')
                st.markdown("**Interaction Modalities:**")
                for mod in modalities:
                    st.markdown(f"- {mod.replace('_', ' ').title()}")

    # Phase 5: Pedagogical Features
    if pd.notna(paper['pedagogical_features']):
        st.subheader("Pedagogical Features")
        features = paper['pedagogical_features'].split(',')
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Features:**")
            for feat in features[:len(features)//2]:
                st.markdown(f"- {feat.replace('_', ' ').title()}")

        with col2:
            for feat in features[len(features)//2:]:
                st.markdown(f"- {feat.replace('_', ' ').title()}")

        if pd.notna(paper['personalization']):
            st.markdown(f"**Personalization:** {paper['personalization'].replace('_', ' ').title()}")

    # Phase 6: Evaluation
    if pd.notna(paper['empirical_evaluation']) and paper['empirical_evaluation'] != 'no_evaluation':
        st.subheader("Evaluation")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Evaluation Type:** {paper['empirical_evaluation'].replace('_', ' ').title()}")
            if pd.notna(paper['sample_size']):
                st.markdown(f"**Sample Size:** {paper['sample_size'].replace('_', ' ').title()}")

        with col2:
            if pd.notna(paper['evaluation_duration']):
                st.markdown(f"**Duration:** {paper['evaluation_duration'].replace('_', ' ').title()}")
            if pd.notna(paper['aspects_evaluated']):
                aspects = paper['aspects_evaluated'].split(',')
                st.markdown("**Aspects Evaluated:**")
                for aspect in aspects:
                    st.markdown(f"- {aspect.replace('_', ' ').title()}")

    # Phase 7: Implementation Context (if applicable)
    if paper['is_implementation'] and pd.notna(paper['institution_type']):
        st.subheader("Implementation Context")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Institution Type:** {paper['institution_type'].replace('_', ' ').title()}")
            if pd.notna(paper['development_approach']):
                st.markdown(f"**Development Approach:** {paper['development_approach'].replace('_', ' ').title()}")

        with col2:
            if pd.notna(paper['language_support']):
                st.markdown(f"**Language Support:** {paper['language_support'].replace('_', ' ').title()}")

    # Phase 8: Additional Information
    if any(pd.notna(paper[col]) for col in ['privacy_protection', 'cost_requirements', 'reference_architecture']):
        st.subheader("Additional Information")
        if pd.notna(paper['privacy_protection']) and paper['privacy_protection'] != 'not_mentioned':
            st.markdown(f"**Privacy Protection:** {paper['privacy_protection'].replace('_', ' ').title()}")
        if pd.notna(paper['cost_requirements']) and paper['cost_requirements'] != 'not_discussed':
            st.markdown(f"**Cost/Resources:** {paper['cost_requirements'].replace('_', ' ').title()}")
        if pd.notna(paper['reference_architecture']) and paper['reference_architecture'] != 'not_clear':
            st.markdown(f"**Reference Architecture:** {paper['reference_architecture'].replace('_', ' ').title()}")

    # Assessment metadata
    if pd.notna(paper['assessment_date']):
        st.caption(f"Assessment performed on: {pd.to_datetime(paper['assessment_date']).strftime('%Y-%m-%d %H:%M')}")

    # PDF link if available
    if pd.notna(paper['file_path']):
        file_name = Path(paper['file_path']).name
        full_path = Path(papers_dir) / file_name

        if full_path.exists():
            with open(full_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=file_name,
                    mime="application/pdf"
                )

            # Optionally, display PDF in iframe if desired
            if st.checkbox("Show PDF Preview"):
                st.markdown("### PDF Preview")
                st.markdown(f'<iframe src="data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}" width="100%" height="800px"></iframe>', unsafe_allow_html=True)


def papers_view(filters=None):
    """
    Displays a Streamlit view for assessing and managing virtual tutor papers, including
    features such as filtering, selection of papers, status visualization, and export
    capability for selected papers.

    Parameters:
    filters: Optional[dict]
        A dictionary containing filter criteria for narrowing down the list of papers.
        If None, no filters are applied, and all papers are displayed.

    Raises:
    sqlite3.OperationalError
        If there is a database error while loading paper details.
    """
    st.title("Virtual Tutor Paper Assessments")

    # Load all paper details
    try:
        papers_df = load_paper_details()
    except sqlite3.OperationalError as e:
        st.error(f"Database error: {e}")
        st.stop()

    if papers_df.empty:
        st.warning("No papers found in the database.")
        st.stop()

    # Apply filters if provided
    if filters:
        filtered_df = apply_filters(papers_df, filters)
    else:
        filtered_df = papers_df

    # Show number of filtered papers
    if filters:
        st.info(f"Showing {len(filtered_df)} of {len(papers_df)} papers based on current filters")

    if filtered_df.empty:
        st.warning("No papers match the current filter criteria.")
        return

    # Paper selection
    st.subheader("Select a Paper")
    col1, col2 = st.columns([2, 1])

    with col1:
        # Add status to the display format
        def format_paper_title(row):
            status = f"[{row['assessment_status']}] "
            title = row['title'][:100] + "..." if len(row['title']) > 100 else row['title']
            return status + title

        # Create selection options
        paper_options = filtered_df.apply(format_paper_title, axis=1).tolist()
        selected_paper_title = st.selectbox(
            "Choose a paper to view",
            paper_options,
            index=0 if paper_options else None
        )

    with col2:
        # Add status distribution
        status_counts = filtered_df['assessment_status'].value_counts()
        st.write("Status Distribution:")
        for status, count in status_counts.items():
            st.write(f"- {status}: {count}")

    # Display selected paper
    if selected_paper_title:
        # Extract original title from formatted selection
        original_title = selected_paper_title.split('] ', 1)[1].split('...')[0]
        paper = filtered_df[filtered_df['title'].str.startswith(original_title)].iloc[0]
        display_paper_details(paper)

        # Export functionality
        if st.button("Export Paper Details"):
            paper_dict = paper.to_dict()
            export_df = pd.DataFrame([paper_dict])
            csv = export_df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"paper_{paper['id']}.csv",
                "text/csv",
                key='download-csv'
            )
