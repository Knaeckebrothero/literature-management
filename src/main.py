"""
This is the main script for the literature management application.
It provides a streamlit interface to import citations, process papers, and view the database.
"""
import streamlit as st
import pandas as pd
import sqlite3
import json
import logging
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from datetime import datetime
from dotenv import find_dotenv, load_dotenv
from process_papers import PdfProcessor
from pathlib import Path
from import_citations import CitationProcessor
from view_paper import papers_view


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@st.cache_resource
def get_connection():
    """Get database connection, creating tables if they don't exist"""
    conn = sqlite3.connect('literature.db', check_same_thread=False)

    # Check if tables exist
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='papers'")
    if cursor.fetchone() is None:
        # Database needs initialization
        setup_database_with_connection(conn)

    return conn


def setup_database_with_connection(conn, schema_path='src/schema.sql'):
    """Setup database using schema.sql file with existing connection"""
    cursor = conn.cursor()

    try:
        # Check if schema file exists
        if not Path(schema_path).exists():
            st.error(f"Schema file '{schema_path}' not found!")
            st.info("Make sure schema.sql is in the same directory as main.py")
            raise FileNotFoundError(f"Schema file '{schema_path}' not found")

        # Read schema from file
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Execute the schema
        conn.executescript(schema_sql)

        # Commit changes
        conn.commit()

        # Log success
        logger.info(f"Database initialized successfully using {schema_path}")

    except FileNotFoundError as e:
        logger.error(f"Schema file error: {e}")
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error during schema creation: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database setup: {e}")
        raise


def load_data_with_lists(base_query=None):
    """Load data including normalized list fields"""
    try:
        conn = get_connection()

        # Use the provided query or default
        query = base_query if base_query else get_all_papers_query()
        papers_df = pd.read_sql_query(query, conn)

        if papers_df.empty:
            return papers_df

        # Add list fields using GROUP_CONCAT
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
            try:
                list_df = pd.read_sql_query(query, conn)
                if not list_df.empty:
                    papers_df = papers_df.merge(
                        list_df,
                        left_on='id',
                        right_on='paper_id',
                        how='left'
                    )
                    # Drop the duplicate paper_id column
                    if 'paper_id' in papers_df.columns and 'id' in papers_df.columns:
                        papers_df = papers_df.drop('paper_id', axis=1)
            except Exception:
                # Table might not exist yet, skip
                pass

        # Convert SQLite integer boolean columns to Python boolean
        bool_columns = ['is_virtual_tutor', 'is_implementation']
        for col in bool_columns:
            if col in papers_df.columns:
                papers_df[col] = papers_df[col].astype('Int64')
                papers_df[col] = papers_df[col] == 1

        return papers_df

    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            # Return empty dataframe if tables don't exist yet
            return pd.DataFrame()
        raise


def get_all_papers_query():
    """Return the standard query for loading all papers with their assessment status"""
    return """
           SELECT
               p.*,
               a.is_virtual_tutor,
               a.is_implementation,
               a.deployment_status,
               a.llm_model,
               a.uses_rag,
               a.primary_function,
               a.subject_domain,
               a.generates_assessments,
               a.publication_type as assessment_publication_type,
               a.availability,
               a.lms_integration,
               a.personalization,
               a.supports_collaboration,
               a.empirical_evaluation,
               a.sample_size,
               a.evaluation_duration,
               a.institution_type,
               a.development_approach,
               a.language_support,
               a.privacy_protection,
               a.cost_requirements,
               a.reference_architecture,
               a.assessment_date,
               CASE
                   WHEN a.paper_id IS NULL THEN 'Unassessed'
                   WHEN a.is_virtual_tutor = 1 THEN 'Virtual Tutor'
                   ELSE 'Not Virtual Tutor'
                   END as assessment_status
           FROM papers p
                    LEFT JOIN virtual_tutor_assessments a ON p.id = a.paper_id
           """


def load_data(query):
    """Load data from the database, ensuring we get ALL papers including unassessed ones."""
    conn = get_connection()

    # Use the standard query if none provided
    query_to_use = query if query else get_all_papers_query()
    df = pd.read_sql_query(query_to_use, conn)

    # Convert SQLite integer boolean columns to Python boolean
    bool_columns = ['is_virtual_tutor', 'is_implementation']
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].astype('Int64')  # Use nullable integer type
            df[col] = df[col] == 1  # Convert to boolean while preserving NULL

    return df


def setup_database(db_path: str = 'literature.db'):
    """
    Function to create the SQLite database, set up the connection
    and create citation and assessment tables if needed.
    """
    conn = sqlite3.connect(db_path)

    # Check if papers table exists with old schema
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='papers'")
    if cursor.fetchone():
        # Table exists, check if DOI has NOT NULL constraint
        cursor.execute("PRAGMA table_info(papers)")
        columns = cursor.fetchall()

        for col in columns:
            if col[1] == 'doi' and col[3] == 1:  # NOT NULL constraint exists
                st.warning("Database schema needs update to support arXiv papers without DOIs.")
                st.info("Please run: `python migrate_database.py` to update your database schema.")
                break

    setup_database_with_connection(conn)
    conn.close()


def import_citations():
    # Configure base path for search results
    search_dir = Path('search_results')

    # Configure files with relative paths - ONLY include files that exist
    file_config = {
        'ieee': [search_dir / 'ieee.csv'],
        'bibtex': [
            search_dir / 'acm.bib',
            search_dir / 'ScienceDirect_1.bib',
            search_dir / 'ScienceDirect_2.bib',
            # search_dir / 'wiley_1.bib',
            # search_dir / 'wiley_2.bib'
        ],
        'springer': [
            search_dir / 'SpringerLink_1.csv',
            search_dir / 'SpringerLink_2.csv'
        ],
    }

    processor = CitationProcessor()
    processor.process_files(file_config)


def process_papers():
    processor = PdfProcessor()
    try:
        processor.process_directory('papers')
    finally:
        processor.close()


def import_arxiv_papers(directory_path: str):
    """Import arXiv papers from a directory"""
    processor = PdfProcessor()
    try:
        processor.process_directory(directory_path, create_missing=True)
    finally:
        processor.close()


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def display_papers_tab(papers_df):
    """Display the papers tab with basic statistics and visualizations."""
    st.title("Papers")

    if papers_df.empty:
        st.warning("No papers match the current filter criteria")
        return

    # Basic statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Papers", len(papers_df))
    with col2:
        st.metric("Unique Venues", papers_df['venue'].nunique())
    with col3:
        year_range = f"{papers_df['publication_year'].min()}-{papers_df['publication_year'].max()}"
        st.metric("Year Range", year_range)

    # Publications per year
    st.subheader("Publications per Year")
    year_counts = papers_df['publication_year'].value_counts().sort_index()
    df_years = pd.DataFrame({
        'Year': year_counts.index,
        'Publications': year_counts.values
    }).reset_index(drop=True)

    if not df_years.empty:
        fig = px.bar(df_years, x='Year', y='Publications')
        fig.update_layout(
            xaxis_title="Year",
            yaxis_title="Number of Publications",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No publication year data available for the current selection")

    # Top venues
    st.subheader("Top Publication Venues")
    venue_counts = papers_df['venue'].value_counts().head(10)
    df_venues = pd.DataFrame({
        'Venue': venue_counts.index,
        'Publications': venue_counts.values
    }).reset_index(drop=True)

    if not df_venues.empty:
        fig = px.bar(df_venues, x='Publications', y='Venue', orientation='h')
        fig.update_layout(
            xaxis_title="Number of Publications",
            yaxis_title="",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No venue data available for the current selection")

    # Publication sources distribution
    st.subheader("Distribution by Publication Source")
    source_counts = papers_df['publication_source'].value_counts()
    df_sources = pd.DataFrame({
        'Source': source_counts.index,
        'Count': source_counts.values
    }).reset_index(drop=True)

    if not df_sources.empty:
        fig = px.pie(df_sources, values='Count', names='Source')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No publication source data available for the current selection")

    # Interactive table
    st.subheader("Papers Database")
    display_cols = [
        'title', 'authors', 'publication_year', 'venue',
        'publication_type', 'publication_source', 'doi', 'volume'
    ]

    # Create a display dataframe with formatted DOI/arXiv ID
    display_df = papers_df[display_cols].copy()
    display_df['ID'] = display_df.apply(
        lambda row: row['doi'] if pd.notna(row['doi']) else
        (f"arXiv:{row['volume']}" if pd.notna(row['volume']) and row['publication_source'] == 'arxiv_auto_import' else 'N/A'),
        axis=1
    )

    # Reorder columns
    final_cols = ['title', 'authors', 'publication_year', 'venue', 'publication_type', 'publication_source', 'ID']

    st.dataframe(
        display_df[final_cols],
        hide_index=True,
        use_container_width=True
    )


def add_paper():
    st.title("Add Paper")

    # Form for paper details
    with st.form("paper_form"):
        doi = st.text_input("DOI", help="Digital Object Identifier (optional for preprints)")
        title = st.text_input("Title*", help="Paper title (required)")
        year = st.number_input("Publication Year*", min_value=1900, max_value=2100, value=2024)
        authors = st.text_input("Authors*", help="Comma-separated list of authors")
        venue = st.text_input("Venue", help="Journal or conference name")
        volume = st.text_input("Volume/arXiv ID", help="Volume number or arXiv identifier")
        publication_type = st.selectbox(
            "Publication Type",
            ["journal_article", "conference_paper", "preprint", "technical_report", "thesis_dissertation", "other"]
        )
        publication_source = st.text_input("Publication Source", help="Where this paper was found")

        submitted = st.form_submit_button("Add Paper")

        if submitted:
            if not all([title, authors]):
                st.error("Please fill in all required fields (marked with *)")
                return

            conn = get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                               INSERT INTO papers
                               (doi, title, publication_year, authors, venue, volume, publication_type, publication_source)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                               """, (
                                   doi or None,  # Use None for NULL instead of empty string
                                   title,
                                   year,
                                   authors,
                                   venue,
                                   volume,
                                   publication_type,
                                   publication_source
                               ))

                conn.commit()
                st.success("Paper added successfully!")
            except sqlite3.IntegrityError:
                st.error("A paper with this DOI already exists in the database")
            except Exception as e:
                st.error(f"Error adding paper: {str(e)}")
            finally:
                conn.close()


def apply_filters(df, filters):
    """Apply filters to a dataframe"""
    filtered_df = df.copy()

    # Debug info before filtering
    print(f"\nInitial dataset size: {len(filtered_df)}")
    print(f"Assessment status distribution:\n{filtered_df['assessment_status'].value_counts(dropna=False)}")

    # Handle year filter
    if filters['years']:
        filtered_df = filtered_df[filtered_df['publication_year'].isin(filters['years'])]
        print(f"\nAfter year filter: {len(filtered_df)} papers")

    # Handle LLM model filter
    if filters['llm_model'] != "All":
        filtered_df = filtered_df[
            filtered_df['llm_model'] == filters['llm_model']
            ]
        print(f"\nAfter LLM model filter: {len(filtered_df)} papers")

    # Handle focus filter
    if filters['focus'] != "All":
        print(f"\nApplying focus filter: {filters['focus']}")
        if filters['focus'] == "Virtual Tutor":
            filtered_df = filtered_df[filtered_df['assessment_status'] == 'Virtual Tutor']
        elif filters['focus'] == "Implementation":
            filtered_df = filtered_df[
                (filtered_df['assessment_status'] == 'Virtual Tutor') &
                (filtered_df['is_implementation'] == True)
                ]
        else:  # "Unassessed/Other"
            filtered_df = filtered_df[filtered_df['assessment_status'].isin(['Unassessed', 'Not Virtual Tutor'])]
        print(f"After focus filter: {len(filtered_df)} papers")
        print(f"Assessment status distribution:\n{filtered_df['assessment_status'].value_counts(dropna=False)}")

    # Handle evaluation filter
    if filters['evaluation'] != "All":
        if filters['evaluation'] == "Evaluated":
            filtered_df = filtered_df[
                filtered_df['empirical_evaluation'].isin(['controlled_experiment', 'pilot_study', 'survey_only'])
            ]
        else:
            filtered_df = filtered_df[
                (filtered_df['empirical_evaluation'].isin(['no_evaluation', 'not_specified'])) |
                (filtered_df['empirical_evaluation'].isna())
                ]
        print(f"\nAfter evaluation filter: {len(filtered_df)} papers")

    return filtered_df


def create_filters(papers_df):
    """Create filter widgets that can be used across tabs"""
    filters = {}

    with st.sidebar:
        st.header("Filters")

        # Year filter
        years = sorted(papers_df['publication_year'].dropna().unique(), reverse=True)
        filters['years'] = st.multiselect(
            "Publication Years",
            years,
            default=years
        )

        # LLM Model filter
        llm_models = papers_df['llm_model'].dropna().unique().tolist()
        llm_models = ["All"] + sorted([model for model in llm_models if pd.notna(model) and model != ''])
        filters['llm_model'] = st.selectbox(
            "LLM Model",
            llm_models
        )

        # Focus filter - updated labels
        filters['focus'] = st.radio(
            "Paper Focus",
            ["All", "Virtual Tutor", "Implementation", "Unassessed/Other"],
            help="""
            - All: Show all papers
            - Virtual Tutor: Papers about virtual tutors (theoretical or implementation)
            - Implementation: Only papers with actual implementations
            - Unassessed/Other: Papers that haven't been assessed or are not about virtual tutors
            """
        )

        # Evaluation filter
        filters['evaluation'] = st.radio(
            "Empirical Evaluation",
            ["All", "Evaluated", "Not Evaluated"]
        )

    return filters


def display_assessments_tab(papers_df, filters):
    """Display the assessments tab with visualizations"""
    st.title("Virtual Tutor Assessments")

    filtered_df = apply_filters(papers_df, filters)

    # Basic statistics with filtered data
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Papers",
            len(filtered_df),
            delta=f"{len(filtered_df) - len(papers_df)} from total"
        )
    with col2:
        if 'is_virtual_tutor' in filtered_df.columns:
            vt_count = len(filtered_df[filtered_df['is_virtual_tutor'] == True])
            st.metric("Virtual Tutor Papers", vt_count)
        else:
            st.metric("Virtual Tutor Papers", "N/A")
    with col3:
        if 'is_implementation' in filtered_df.columns:
            impl_count = len(filtered_df[filtered_df['is_implementation'] == True])
            st.metric("Implementation Papers", impl_count)
        else:
            st.metric("Implementation Papers", "N/A")

    # Convert to regular Python types for JSON serialization
    filtered_data = filtered_df.to_dict(orient='records')
    filters_json = {k: [int(x) if isinstance(x, np.integer) else x for x in v]
    if isinstance(v, (list, np.ndarray)) else v
                    for k, v in filters.items()}

    # Additional visualizations
    st.subheader("Key Insights")

    with st.expander("LLM Model Distribution"):
        if 'llm_model' in filtered_df.columns:
            model_counts = filtered_df['llm_model'].value_counts()
            if not model_counts.empty:
                fig = px.pie(
                    values=model_counts.values,
                    names=model_counts.index,
                    title="Distribution of LLM Models Used"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No LLM model information available.")
        else:
            st.write("LLM model information not available.")

    with st.expander("Primary Functions"):
        if 'primary_function' in filtered_df.columns:
            function_counts = filtered_df['primary_function'].value_counts()
            if not function_counts.empty:
                fig = px.bar(
                    x=function_counts.values,
                    y=function_counts.index,
                    orientation='h',
                    title="Primary Functions of Virtual Tutors"
                )
                fig.update_layout(yaxis_title="Function", xaxis_title="Number of Papers")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No primary function information available.")
        else:
            st.write("Primary function information not available.")

    with st.expander("Evaluation Types"):
        if 'empirical_evaluation' in filtered_df.columns:
            eval_counts = filtered_df['empirical_evaluation'].value_counts()
            if not eval_counts.empty:
                fig = px.bar(
                    x=eval_counts.index,
                    y=eval_counts.values,
                    title="Types of Empirical Evaluations"
                )
                fig.update_layout(xaxis_title="Evaluation Type", yaxis_title="Number of Papers")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No evaluation information available.")
        else:
            st.write("Evaluation information not available.")


@st.cache_data
def load_keyword_data():
    """Load keyword data with relationships and paper metadata"""
    conn = get_connection()
    query = """
            SELECT
                k.keyword,
                k.id as keyword_id,
                p.publication_year,
                p.id as paper_id,
                p.publication_source,
                pa.llm_model,
                pa.is_virtual_tutor,
                pa.is_implementation
            FROM keywords k
                     JOIN rel_keywords_papers r ON k.id = r.keyword_id
                     JOIN papers p ON r.paper_id = p.id
                     LEFT JOIN virtual_tutor_assessments pa ON p.id = pa.paper_id \
            """
    return pd.read_sql_query(query, conn)


@st.cache_data
def process_keyword_network(df, max_nodes=30):
    """Process keyword data for network visualization with size limits"""
    # Get top keywords first to limit network size
    top_keywords = df['keyword'].value_counts().head(max_nodes).index
    df_filtered = df[df['keyword'].isin(top_keywords)]

    # Create co-occurrence matrix
    paper_keyword_groups = df_filtered.groupby('paper_id')['keyword'].agg(list)
    keyword_pairs = []

    for keywords in paper_keyword_groups:
        if len(keywords) > 1:  # Only process if there are at least 2 keywords
            for i in range(len(keywords)):
                for j in range(i + 1, len(keywords)):
                    keyword_pairs.append(tuple(sorted([keywords[i], keywords[j]])))

    # Count co-occurrences
    co_occurrences = pd.DataFrame(
        keyword_pairs,
        columns=['source', 'target']
    ).value_counts().reset_index()
    co_occurrences.columns = ['source', 'target', 'weight']

    return co_occurrences


@st.cache_data
def process_temporal_evolution(df, top_n=10):
    """Process keyword data for temporal evolution"""
    top_keywords = df['keyword'].value_counts().head(top_n).index
    mask = df['keyword'].isin(top_keywords)
    return df[mask].groupby(['publication_year', 'keyword']).size().reset_index(name='count')


@st.cache_data
def process_keyword_frequency(df, top_n=20):
    """Process keyword frequency data"""
    return df['keyword'].value_counts().head(top_n).reset_index()


def display_keywords_tab(papers_df, filters):
    """Display the keywords analysis tab"""
    st.title("Keyword Analysis")

    with st.spinner("Loading keyword data..."):
        keyword_data = load_keyword_data()
        filtered_df = apply_filters(papers_df, filters)
        filtered_keywords = keyword_data[
            keyword_data['paper_id'].isin(filtered_df['id'])
        ]

    if filtered_keywords.empty:
        st.warning("No keyword data available for the current selection.")
        return

    # Add controls for visualization parameters
    with st.expander("Visualization Settings"):
        col1, col2 = st.columns(2)
        with col1:
            max_nodes = st.slider("Max number of keywords in network", 5, 50, 30)
            top_n_temporal = st.slider("Number of keywords in temporal view", 5, 20, 10)
        with col2:
            top_n_freq = st.slider("Number of keywords in frequency view", 5, 50, 20)
            min_cooccurrence = st.slider("Minimum co-occurrence strength", 1, 10, 2)

    # Create two columns for the top section
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Keyword Co-occurrence Network")
        with st.spinner("Generating network visualization..."):
            network_data = process_keyword_network(filtered_keywords, max_nodes)
            network_data = network_data[network_data['weight'] >= min_cooccurrence]

            if network_data.empty:
                st.warning("Not enough co-occurring keywords found with current settings.")
                return

            import networkx as nx
            G = nx.from_pandas_edgelist(
                network_data,
                'source',
                'target',
                edge_attr='weight'
            )

            if len(G.nodes()) > 0:
                pos = nx.spring_layout(G, k=1/np.sqrt(len(G.nodes())), iterations=50)

                # Create separate traces for each edge with weight-dependent width
                edge_traces = []
                for edge in G.edges(data=True):
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    weight = edge[2].get('weight', 1)

                    edge_trace = go.Scatter(
                        x=[x0, x1],
                        y=[y0, y1],
                        line=dict(
                            width=weight/network_data['weight'].max() * 5,
                            color='#888'
                        ),
                        hoverinfo='text',
                        text=f"Weight: {weight}",
                        mode='lines'
                    )
                    edge_traces.append(edge_trace)

                # Create nodes trace
                node_x = [pos[node][0] for node in G.nodes()]
                node_y = [pos[node][1] for node in G.nodes()]
                node_text = list(G.nodes())

                node_trace = go.Scatter(
                    x=node_x,
                    y=node_y,
                    mode='markers+text',
                    hoverinfo='text',
                    text=node_text,
                    textposition="top center",
                    marker=dict(
                        size=10,
                        color='lightblue',
                        line_width=2
                    )
                )

                # Combine all traces
                fig = go.Figure(
                    data=edge_traces + [node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0,l=0,r=0,t=0),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                    )
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Not enough connected keywords to create network visualization")

    with col2:
        st.subheader("Keyword Frequency")
        with st.spinner("Generating frequency visualization..."):
            freq_data = process_keyword_frequency(filtered_keywords, top_n_freq)
            fig = px.bar(
                freq_data,
                x='count',
                y='keyword',
                orientation='h',
                title='Most Common Keywords'
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Temporal Keyword Evolution")
    with st.spinner("Generating temporal visualization..."):
        temporal_data = process_temporal_evolution(filtered_keywords, top_n_temporal)
        fig = px.line(
            temporal_data,
            x='publication_year',
            y='count',
            color='keyword',
            title='Keyword Usage Over Time'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Add export functionality
    st.subheader("Export Data")
    col1, col2, col3 = st.columns(3)

    with col1:
        csv = network_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Co-occurrence Data",
            csv,
            "keyword_network.csv",
            "text/csv",
            key='download-network'
        )

    with col2:
        csv = temporal_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Temporal Data",
            csv,
            "keyword_temporal.csv",
            "text/csv",
            key='download-temporal'
        )

    with col3:
        csv = freq_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Download Frequency Data",
            csv,
            "keyword_frequency.csv",
            "text/csv",
            key='download-frequency'
        )


def display_analysis_tab(papers_df, filters):
    """Display comprehensive analysis tab with multiple visualization sub-tabs"""
    st.title("📊 Comprehensive Analysis Dashboard")

    # Apply filters
    filtered_df = apply_filters(papers_df, filters)

    # Only include assessed papers for most analyses
    assessed_df = filtered_df[filtered_df['assessment_date'].notna()].copy()
    vt_df = assessed_df[assessed_df['is_virtual_tutor'] == True].copy()

    if assessed_df.empty:
        st.warning("No assessed papers found. Please run assessments first.")
        return

    # Create sub-tabs for different analysis types
    tabs = st.tabs([
        "📈 Overview",
        "🤖 LLM Technology",
        "🏗️ Architecture",
        "📚 Pedagogical Features",
        "📊 Evaluation Insights",
        "🏛️ Implementation Context",
        "🔒 Privacy & Compliance",
        "🔍 Comparative Analysis",
        "🎯 Research Gaps",
        "📋 Summary Report"
    ])

    with tabs[0]:
        display_assessment_overview(filtered_df, assessed_df, vt_df)

    with tabs[1]:
        display_llm_technology_analysis(vt_df)

    with tabs[2]:
        display_architecture_analysis(vt_df)

    with tabs[3]:
        display_pedagogical_analysis(vt_df)

    with tabs[4]:
        display_evaluation_insights(vt_df)

    with tabs[5]:
        display_implementation_context(vt_df)

    with tabs[6]:
        display_privacy_compliance(vt_df)

    with tabs[7]:
        display_comparative_analysis(vt_df)

    with tabs[8]:
        display_research_gaps(vt_df, assessed_df)

    with tabs[9]:
        display_summary_report(filtered_df, assessed_df, vt_df)


def display_assessment_overview(all_df, assessed_df, vt_df):
    """Display overview metrics and timeline"""
    st.header("Assessment Overview Dashboard")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    total_papers = len(all_df)
    assessed = len(assessed_df)
    virtual_tutors = len(vt_df)
    implementations = len(vt_df[vt_df['is_implementation'] == True])

    col1.metric("Assessment Progress",
                f"{assessed}/{total_papers}",
                f"{(assessed/total_papers*100):.1f}%" if total_papers > 0 else "0%")

    col2.metric("Virtual Tutors",
                virtual_tutors,
                f"{(virtual_tutors/assessed*100):.1f}% of assessed" if assessed > 0 else "0%")

    col3.metric("Implementations",
                implementations,
                f"{(implementations/virtual_tutors*100):.1f}% of VT" if virtual_tutors > 0 else "0%")

    col4.metric("Theoretical Papers",
                virtual_tutors - implementations)

    # Assessment timeline
    if 'assessment_date' in assessed_df.columns:
        st.subheader("Assessment Timeline")
        assessed_df['assessment_date_clean'] = pd.to_datetime(assessed_df['assessment_date'])
        timeline_df = assessed_df.groupby(assessed_df['assessment_date_clean'].dt.date).size().reset_index()
        timeline_df.columns = ['Date', 'Papers Assessed']

        fig = px.line(timeline_df, x='Date', y='Papers Assessed',
                      title="Papers Assessed Over Time", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    # Assessment status distribution
    col1, col2 = st.columns(2)

    with col1:
        status_counts = all_df['assessment_status'].value_counts()
        fig = px.pie(values=status_counts.values, names=status_counts.index,
                     title="Assessment Status Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Publication year vs assessment status
        year_status = all_df.groupby(['publication_year', 'assessment_status']).size().reset_index(name='count')
        fig = px.bar(year_status, x='publication_year', y='count', color='assessment_status',
                     title="Assessment Status by Publication Year")
        st.plotly_chart(fig, use_container_width=True)


def display_llm_technology_analysis(vt_df):
    """Display LLM technology landscape analysis"""
    st.header("🤖 LLM Technology Analysis")

    if vt_df.empty:
        st.warning("No virtual tutor papers found.")
        return

    # Sunburst chart: LLM Model → Primary Function → Subject Domain
    st.subheader("LLM Technology Landscape")

    # Check if required columns exist
    required_cols = ['llm_model', 'primary_function', 'subject_domain']
    missing_cols = [col for col in required_cols if col not in vt_df.columns]

    if missing_cols:
        st.warning(f"Missing columns for sunburst chart: {', '.join(missing_cols)}")
        st.info("This may be because papers haven't been fully assessed yet.")
    else:
        # Prepare data for sunburst
        sunburst_df = vt_df[required_cols].copy()
        sunburst_df = sunburst_df.dropna()

        if not sunburst_df.empty:
            fig = px.sunburst(sunburst_df,
                              path=['llm_model', 'primary_function', 'subject_domain'],
                              title="Hierarchical View: LLM Model → Function → Domain")
            fig.update_traces(textinfo="label+percent parent")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No complete data available for sunburst visualization.")

    # Heatmap: LLM Model vs Deployment Status
    col1, col2 = st.columns(2)

    with col1:
        if 'deployment_status' in vt_df.columns and 'llm_model' in vt_df.columns:
            heatmap_df = vt_df[['llm_model', 'deployment_status']].dropna()
            if not heatmap_df.empty:
                heatmap_data = pd.crosstab(heatmap_df['llm_model'], heatmap_df['deployment_status'])
                fig = px.imshow(heatmap_data,
                                labels=dict(x="Deployment Status", y="LLM Model", color="Count"),
                                title="LLM Models by Deployment Status",
                                aspect="auto")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No deployment status data available.")
        else:
            st.info("Deployment status information not available.")

    with col2:
        # Timeline: Evolution of LLM adoption
        if 'llm_model' in vt_df.columns:
            llm_timeline_df = vt_df[['publication_year', 'llm_model']].dropna()
            if not llm_timeline_df.empty:
                llm_timeline = llm_timeline_df.groupby(['publication_year', 'llm_model']).size().reset_index(name='count')
                fig = px.line(llm_timeline, x='publication_year', y='count', color='llm_model',
                              title="LLM Adoption Timeline", markers=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No LLM timeline data available.")
        else:
            st.info("LLM model information not available.")

    # RAG adoption analysis
    st.subheader("RAG (Retrieval-Augmented Generation) Analysis")
    col1, col2 = st.columns(2)

    with col1:
        if 'uses_rag' in vt_df.columns:
            rag_df = vt_df['uses_rag'].dropna()
            if not rag_df.empty:
                rag_counts = rag_df.value_counts()
                fig = px.pie(values=rag_counts.values, names=rag_counts.index,
                             title="RAG Adoption in Virtual Tutors")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No RAG usage data available.")
        else:
            st.info("RAG information not available.")

    with col2:
        # RAG usage by LLM model
        if 'llm_model' in vt_df.columns and 'uses_rag' in vt_df.columns:
            rag_llm_df = vt_df[['llm_model', 'uses_rag']].dropna()
            if not rag_llm_df.empty:
                rag_by_llm = pd.crosstab(rag_llm_df['llm_model'], rag_llm_df['uses_rag'])
                fig = px.bar(rag_by_llm.T, title="RAG Usage by LLM Model", barmode='group')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No RAG by LLM model data available.")
        else:
            st.info("Insufficient data for RAG by LLM analysis.")


def display_architecture_analysis(vt_df):
    """Display technical architecture patterns analysis"""
    st.header("🏗️ Technical Architecture Analysis")

    # LMS Integration distribution
    st.subheader("LMS Integration Patterns")
    col1, col2 = st.columns(2)

    with col1:
        if 'lms_integration' in vt_df.columns:
            lms_counts = vt_df['lms_integration'].value_counts()
            fig = px.bar(x=lms_counts.values, y=lms_counts.index, orientation='h',
                         title="LMS Integration Types")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Architecture components analysis
        if 'architecture_components' in vt_df.columns:
            # Split comma-separated values and count
            all_components = []
            for components in vt_df['architecture_components'].dropna():
                if components:
                    all_components.extend([c.strip() for c in components.split(',')])

            if all_components:
                component_counts = pd.Series(all_components).value_counts()
                fig = px.bar(x=component_counts.values, y=component_counts.index,
                             orientation='h', title="Architecture Components Frequency")
                st.plotly_chart(fig, use_container_width=True)

    # Interaction modalities
    st.subheader("Interaction Modalities")
    if 'interaction_modality' in vt_df.columns:
        # Process interaction modalities
        all_modalities = []
        for modalities in vt_df['interaction_modality'].dropna():
            if modalities:
                all_modalities.extend([m.strip() for m in modalities.split(',')])

        if all_modalities:
            modality_counts = pd.Series(all_modalities).value_counts()
            fig = px.pie(values=modality_counts.values, names=modality_counts.index,
                         title="Distribution of Interaction Modalities")
            st.plotly_chart(fig, use_container_width=True)

    # Analytics features
    st.subheader("Learning Analytics Features")
    if 'analytics_features' in vt_df.columns:
        all_analytics = []
        for features in vt_df['analytics_features'].dropna():
            if features and features != 'none_mentioned':
                all_analytics.extend([f.strip() for f in features.split(',')])

        if all_analytics:
            analytics_counts = pd.Series(all_analytics).value_counts()
            fig = px.bar(analytics_counts, orientation='h',
                         title="Analytics Features Implementation",
                         labels={'value': 'Count', 'index': 'Feature'})
            st.plotly_chart(fig, use_container_width=True)


def display_pedagogical_analysis(vt_df):
    """Display pedagogical features analysis"""
    st.header("📚 Pedagogical Features Analysis")

    # Pedagogical features heatmap
    st.subheader("Pedagogical Features Implementation")

    if 'pedagogical_features' in vt_df.columns:
        # Create a matrix of papers vs features
        feature_matrix = []
        paper_titles = []

        for idx, row in vt_df.iterrows():
            if pd.notna(row['pedagogical_features']) and row['pedagogical_features']:
                features = [f.strip() for f in row['pedagogical_features'].split(',')]
                feature_matrix.append(features)
                paper_titles.append(row['title'][:50] + '...' if len(row['title']) > 50 else row['title'])

        if feature_matrix:
            # Get all unique features
            all_features = set()
            for features in feature_matrix:
                all_features.update(features)
            all_features = sorted(list(all_features))

            # Create binary matrix
            matrix_data = []
            for features in feature_matrix:
                row = [1 if f in features else 0 for f in all_features]
                matrix_data.append(row)

            if len(paper_titles) <= 20:  # Only show heatmap for reasonable number of papers
                df_matrix = pd.DataFrame(matrix_data, index=paper_titles, columns=all_features)
                fig = px.imshow(df_matrix,
                                labels=dict(x="Features", y="Papers", color="Implemented"),
                                title="Pedagogical Features by Paper",
                                aspect="auto",
                                color_continuous_scale="Blues")
                st.plotly_chart(fig, use_container_width=True)

            # Feature frequency
            feature_counts = pd.Series([f for features in feature_matrix for f in features]).value_counts()
            fig = px.bar(x=feature_counts.values, y=feature_counts.index, orientation='h',
                         title="Pedagogical Features Frequency")
            st.plotly_chart(fig, use_container_width=True)

    # Personalization and collaboration analysis
    col1, col2 = st.columns(2)

    with col1:
        if 'personalization' in vt_df.columns:
            personal_counts = vt_df['personalization'].value_counts()
            fig = px.pie(values=personal_counts.values, names=personal_counts.index,
                         title="Personalization Approaches")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'supports_collaboration' in vt_df.columns:
            collab_counts = vt_df['supports_collaboration'].value_counts()
            fig = px.pie(values=collab_counts.values, names=collab_counts.index,
                         title="Collaboration Support")
            st.plotly_chart(fig, use_container_width=True)

    # Collaboration types
    if 'collaboration_types' in vt_df.columns:
        all_collab_types = []
        for types in vt_df['collaboration_types'].dropna():
            if types:
                all_collab_types.extend([t.strip() for t in types.split(',')])

        if all_collab_types:
            collab_type_counts = pd.Series(all_collab_types).value_counts()
            fig = px.bar(collab_type_counts, orientation='h',
                         title="Types of Collaboration Supported",
                         labels={'value': 'Count', 'index': 'Collaboration Type'})
            st.plotly_chart(fig, use_container_width=True)


def display_evaluation_insights(vt_df):
    """Display evaluation and empirical evidence analysis"""
    st.header("📊 Evaluation Insights")

    # Evaluation overview
    col1, col2 = st.columns(2)

    with col1:
        if 'empirical_evaluation' in vt_df.columns:
            eval_counts = vt_df['empirical_evaluation'].value_counts()
            fig = px.pie(values=eval_counts.values, names=eval_counts.index,
                         title="Types of Empirical Evaluation")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Sample size distribution
        if 'sample_size' in vt_df.columns:
            sample_counts = vt_df['sample_size'].value_counts()
            fig = px.bar(x=sample_counts.index, y=sample_counts.values,
                         title="Sample Size Distribution")
            st.plotly_chart(fig, use_container_width=True)

    # Bubble chart: Sample size vs Duration vs Aspects evaluated
    st.subheader("Evaluation Characteristics")

    eval_df = vt_df[['empirical_evaluation', 'sample_size', 'evaluation_duration', 'aspects_evaluated']].copy()
    eval_df = eval_df[eval_df['empirical_evaluation'] != 'no_evaluation'].dropna(subset=['sample_size'])

    if not eval_df.empty:
        # Map categorical values to numeric for visualization
        size_map = {'less_than_50': 25, '50_to_200': 125, '201_to_500': 350, 'more_than_500': 750}
        duration_map = {'single_session': 1, 'less_than_month': 15, 'one_semester': 120,
                        'multiple_semesters': 240, 'longitudinal': 365}

        eval_df['size_numeric'] = eval_df['sample_size'].map(size_map)
        eval_df['duration_numeric'] = eval_df['evaluation_duration'].map(duration_map)

        # Count aspects evaluated
        eval_df['aspect_count'] = eval_df['aspects_evaluated'].apply(
            lambda x: len(x.split(',')) if pd.notna(x) else 0
        )

        fig = px.scatter(eval_df, x='duration_numeric', y='size_numeric',
                         size='aspect_count', color='empirical_evaluation',
                         hover_data=['sample_size', 'evaluation_duration'],
                         labels={'duration_numeric': 'Duration (days)',
                                 'size_numeric': 'Sample Size',
                                 'aspect_count': 'Aspects Evaluated'},
                         title="Evaluation Scope: Duration vs Sample Size vs Aspects")
        st.plotly_chart(fig, use_container_width=True)

    # Aspects evaluated
    st.subheader("Aspects Evaluated in Studies")
    if 'aspects_evaluated' in vt_df.columns:
        all_aspects = []
        for aspects in vt_df['aspects_evaluated'].dropna():
            if aspects and aspects != 'not_applicable':
                all_aspects.extend([a.strip() for a in aspects.split(',')])

        if all_aspects:
            aspect_counts = pd.Series(all_aspects).value_counts()
            fig = px.bar(x=aspect_counts.values, y=aspect_counts.index, orientation='h',
                         title="Frequency of Evaluated Aspects")
            st.plotly_chart(fig, use_container_width=True)


def display_implementation_context(vt_df):
    """Display implementation context analysis"""
    st.header("🏛️ Implementation Context")

    impl_df = vt_df[vt_df['is_implementation'] == True].copy()

    if impl_df.empty:
        st.warning("No implementation papers found.")
        return

    # Institution types
    col1, col2 = st.columns(2)

    with col1:
        if 'institution_type' in impl_df.columns:
            inst_counts = impl_df['institution_type'].value_counts()
            fig = px.pie(values=inst_counts.values, names=inst_counts.index,
                         title="Institution Types")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Development approach
        if 'development_approach' in impl_df.columns:
            dev_counts = impl_df['development_approach'].value_counts()
            fig = px.bar(x=dev_counts.values, y=dev_counts.index, orientation='h',
                         title="Development Approaches")
            st.plotly_chart(fig, use_container_width=True)

    # Language support analysis
    st.subheader("Language Support")
    if 'language_support' in impl_df.columns:
        lang_counts = impl_df['language_support'].value_counts()
        fig = px.bar(lang_counts, title="Language Support Distribution",
                     labels={'value': 'Count', 'index': 'Language Support'})
        st.plotly_chart(fig, use_container_width=True)

    # Geographic distribution (if venue data provides hints)
    st.subheader("Publication Venues by Region")
    # This is a simplified analysis based on venue names
    venue_regions = {
        'german': ['TU', 'Universität', 'Hochschule', 'FH', 'RWTH', 'LMU'],
        'us': ['MIT', 'Stanford', 'Berkeley', 'CMU', 'Georgia Tech'],
        'uk': ['Oxford', 'Cambridge', 'Imperial', 'UCL'],
        'other': []
    }

    def classify_region(venue):
        if pd.isna(venue):
            return 'Unknown'
        venue_lower = venue.lower()
        for region, keywords in venue_regions.items():
            if any(keyword.lower() in venue_lower for keyword in keywords):
                return region.upper()
        return 'Other'

    impl_df['region'] = impl_df['venue'].apply(classify_region)
    region_counts = impl_df['region'].value_counts()

    fig = px.pie(values=region_counts.values, names=region_counts.index,
                 title="Approximate Regional Distribution (based on venue)")
    st.plotly_chart(fig, use_container_width=True)


def display_privacy_compliance(vt_df):
    """Display privacy and compliance analysis"""
    st.header("🔒 Privacy & Compliance Analysis")

    # Privacy protection overview
    col1, col2 = st.columns(2)

    with col1:
        if 'privacy_protection' in vt_df.columns:
            privacy_counts = vt_df['privacy_protection'].value_counts()
            fig = px.pie(values=privacy_counts.values, names=privacy_counts.index,
                         title="Privacy Protection Measures")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Cost requirements
        if 'cost_requirements' in vt_df.columns:
            cost_counts = vt_df['cost_requirements'].value_counts()
            fig = px.bar(x=cost_counts.values, y=cost_counts.index, orientation='h',
                         title="Cost/Resource Requirements")
            st.plotly_chart(fig, use_container_width=True)

    # GDPR compliance timeline
    st.subheader("Privacy Awareness Over Time")
    if 'privacy_protection' in vt_df.columns and 'publication_year' in vt_df.columns:
        privacy_timeline = pd.crosstab(vt_df['publication_year'], vt_df['privacy_protection'])
        fig = px.bar(privacy_timeline.T, title="Privacy Protection Mentions by Year",
                     barmode='stack')
        st.plotly_chart(fig, use_container_width=True)

    # Reference architecture usage
    st.subheader("Reference Architecture Adoption")
    if 'reference_architecture' in vt_df.columns:
        ref_arch_counts = vt_df['reference_architecture'].value_counts()
        fig = px.pie(values=ref_arch_counts.values, names=ref_arch_counts.index,
                     title="Use of Reference Architectures")
        st.plotly_chart(fig, use_container_width=True)


def display_comparative_analysis(vt_df):
    """Display comparative analysis tools"""
    st.header("🔍 Comparative Analysis")

    # Feature comparison matrix
    st.subheader("Virtual Tutor Feature Comparison")

    # Select papers to compare
    paper_titles = vt_df['title'].tolist()
    if len(paper_titles) > 1:
        selected_papers = st.multiselect(
            "Select papers to compare (max 5):",
            paper_titles,
            default=paper_titles[:min(3, len(paper_titles))],
            max_selections=5
        )

        if selected_papers:
            comparison_df = vt_df[vt_df['title'].isin(selected_papers)].copy()

            # Create comparison matrix
            features_to_compare = [
                'llm_model', 'uses_rag', 'primary_function', 'subject_domain',
                'lms_integration', 'personalization', 'supports_collaboration',
                'empirical_evaluation', 'sample_size', 'privacy_protection'
            ]

            comparison_data = []
            for _, paper in comparison_df.iterrows():
                row_data = {'Title': paper['title'][:50] + '...'}
                for feature in features_to_compare:
                    if feature in paper:
                        row_data[feature.replace('_', ' ').title()] = paper[feature]
                comparison_data.append(row_data)

            comparison_table = pd.DataFrame(comparison_data)
            st.dataframe(comparison_table.set_index('Title'), use_container_width=True)

            # Download comparison
            csv = comparison_table.to_csv(index=False)
            st.download_button(
                "Download Comparison CSV",
                csv,
                "vt_comparison.csv",
                "text/csv"
            )

    # Feature co-occurrence analysis
    st.subheader("Feature Co-occurrence Analysis")

    # Analyze which features often appear together
    feature_pairs = []

    for _, row in vt_df.iterrows():
        # Check pairs of binary features
        binary_features = {
            'uses_rag': row.get('uses_rag') == 'yes',
            'generates_assessments': row.get('generates_assessments') == 'yes',
            'supports_collaboration': row.get('supports_collaboration') == 'yes',
            'has_evaluation': row.get('empirical_evaluation') not in ['no_evaluation', 'not_specified'],
            'is_implementation': row.get('is_implementation') == True
        }

        feature_names = list(binary_features.keys())
        for i in range(len(feature_names)):
            for j in range(i+1, len(feature_names)):
                if binary_features[feature_names[i]] and binary_features[feature_names[j]]:
                    feature_pairs.append((feature_names[i], feature_names[j]))

    if feature_pairs:
        pair_counts = pd.Series(feature_pairs).value_counts()

        # Create network visualization
        G = nx.Graph()
        for (f1, f2), count in pair_counts.items():
            if count > 1:  # Only show pairs that occur more than once
                G.add_edge(f1, f2, weight=count)

        if G.number_of_nodes() > 0:
            pos = nx.spring_layout(G)

            # Create edge trace
            edge_trace = []
            for edge in G.edges(data=True):
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_trace.append(go.Scatter(
                    x=[x0, x1], y=[y0, y1],
                    line=dict(width=edge[2]['weight'], color='#888'),
                    hoverinfo='none',
                    mode='lines'
                ))

            # Create node trace
            node_x = [pos[node][0] for node in G.nodes()]
            node_y = [pos[node][1] for node in G.nodes()]

            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=[node.replace('_', ' ').title() for node in G.nodes()],
                textposition="top center",
                marker=dict(size=20, color='lightblue', line_width=2)
            )

            fig = go.Figure(data=edge_trace + [node_trace],
                            layout=go.Layout(
                                title="Feature Co-occurrence Network",
                                showlegend=False,
                                hovermode='closest',
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                            ))
            st.plotly_chart(fig, use_container_width=True)


def safe_value_counts(df, column, default_message="No data available"):
    """Safely get value counts for a column, handling missing columns"""
    if column in df.columns:
        counts = df[column].dropna().value_counts()
        if not counts.empty:
            return counts
    return None


def display_research_gaps(vt_df, assessed_df):
    """Identify and display research gaps"""
    st.header("🎯 Research Gap Analysis")

    # Under-researched domains
    st.subheader("Under-researched Subject Domains")
    if 'subject_domain' in vt_df.columns:
        domain_counts = vt_df['subject_domain'].value_counts()

        # Define expected domains
        all_domains = ['computer_science', 'mathematics', 'natural_sciences',
                       'engineering', 'languages', 'social_sciences']

        missing_domains = [d for d in all_domains if d not in domain_counts.index]
        under_researched = domain_counts[domain_counts < 3].index.tolist()

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Missing Domains:**")
            if missing_domains:
                for domain in missing_domains:
                    st.write(f"- {domain.replace('_', ' ').title()}")
            else:
                st.write("All major domains have some representation")

        with col2:
            st.write("**Under-researched Domains (<3 papers):**")
            if under_researched:
                for domain in under_researched:
                    count = domain_counts[domain]
                    st.write(f"- {domain.replace('_', ' ').title()}: {count} papers")
            else:
                st.write("All domains have adequate representation")
    else:
        st.info("Subject domain information not available in the dataset.")

    # Missing evaluation types
    st.subheader("Evaluation Gaps")
    if 'empirical_evaluation' in vt_df.columns:
        eval_df = vt_df['empirical_evaluation'].dropna()
        if not eval_df.empty:
            no_eval = len(eval_df[eval_df.isin(['no_evaluation', 'not_specified'])])
            total = len(eval_df)

            if total > 0:
                st.metric("Papers without Evaluation",
                          f"{no_eval}/{total}",
                          f"{(no_eval/total*100):.1f}%")

                # Evaluation type by year
                eval_year_df = vt_df[['publication_year', 'empirical_evaluation']].dropna()
                if not eval_year_df.empty:
                    eval_by_year = pd.crosstab(
                        eval_year_df['publication_year'],
                        eval_year_df['empirical_evaluation'] != 'no_evaluation'
                    )
                    eval_by_year.columns = ['No Evaluation', 'Has Evaluation']

                    fig = px.bar(eval_by_year, title="Evaluation Status by Year",
                                 barmode='stack')
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No evaluation data available.")
    else:
        st.info("Evaluation information not available in the dataset.")

    # LLM model diversity
    st.subheader("LLM Model Coverage")
    if 'llm_model' in vt_df.columns:
        model_df = vt_df['llm_model'].dropna()
        if not model_df.empty:
            model_counts = model_df.value_counts()

            # Expected models
            major_models = ['gpt_35_4', 'claude', 'llama', 'gemini']
            missing_models = [m for m in major_models if m not in model_counts.index]

            if missing_models:
                st.write("**Major LLMs not yet studied:**")
                for model in missing_models:
                    st.write(f"- {model.upper()}")
            else:
                st.write("All major LLM models have been studied.")
        else:
            st.info("No LLM model data available.")
    else:
        st.info("LLM model information not available in the dataset.")

    # Feature implementation gaps
    st.subheader("Feature Implementation Gaps")

    # Calculate implementation rates for key features
    feature_rates = {}

    if 'uses_rag' in vt_df.columns:
        rag_yes = (vt_df['uses_rag'] == 'yes').sum()
        feature_rates['RAG Implementation'] = rag_yes / len(vt_df) * 100 if len(vt_df) > 0 else 0

    if 'generates_assessments' in vt_df.columns:
        gen_yes = (vt_df['generates_assessments'] == 'yes').sum()
        feature_rates['Generates Assessments'] = gen_yes / len(vt_df) * 100 if len(vt_df) > 0 else 0

    if 'supports_collaboration' in vt_df.columns:
        collab_yes = (vt_df['supports_collaboration'] == 'yes').sum()
        feature_rates['Supports Collaboration'] = collab_yes / len(vt_df) * 100 if len(vt_df) > 0 else 0

    if 'personalization' in vt_df.columns:
        personal_yes = (vt_df['personalization'] != 'no_personalization').sum()
        feature_rates['Has Personalization'] = personal_yes / len(vt_df) * 100 if len(vt_df) > 0 else 0

    if 'privacy_protection' in vt_df.columns:
        privacy_yes = (vt_df['privacy_protection'] != 'not_mentioned').sum()
        feature_rates['Privacy Addressed'] = privacy_yes / len(vt_df) * 100 if len(vt_df) > 0 else 0

    if feature_rates:
        rates_df = pd.DataFrame(list(feature_rates.items()), columns=['Feature', 'Implementation Rate'])
        fig = px.bar(rates_df, x='Feature', y='Implementation Rate',
                     title="Feature Implementation Rates (%)",
                     color='Implementation Rate',
                     color_continuous_scale='RdYlGn')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Feature implementation data not available.")


def display_summary_report(all_df, assessed_df, vt_df):
    """Generate and display a comprehensive summary report"""
    st.header("📋 Summary Report")

    st.write("### Executive Summary")

    # Key findings
    total_papers = len(all_df)
    assessed_papers = len(assessed_df)
    vt_papers = len(vt_df)
    impl_papers = len(vt_df[vt_df['is_implementation'] == True])

    summary_text = f"""
    This systematic literature review analyzed **{total_papers} papers** on virtual tutors in higher education. 
    Of these, **{assessed_papers} papers ({assessed_papers/total_papers*100:.1f}%)** have been fully assessed.
    
    **Key Findings:**
    - **{vt_papers} papers** describe virtual tutors using large language models
    - **{impl_papers} papers ({impl_papers/vt_papers*100:.1f}%)** present actual implementations
    - **{vt_papers - impl_papers} papers** are theoretical or conceptual
    
    **Technology Landscape:**
    """
    st.write(summary_text)

    # Top technologies
    if 'llm_model' in vt_df.columns:
        top_llms = vt_df['llm_model'].value_counts().head(3)
        st.write("**Most Used LLMs:**")
        for llm, count in top_llms.items():
            st.write(f"- {llm}: {count} papers ({count/vt_papers*100:.1f}%)")

    # Research recommendations
    st.write("### Research Recommendations")

    recommendations = []

    # Check for evaluation gaps
    if 'empirical_evaluation' in vt_df.columns:
        no_eval_rate = (vt_df['empirical_evaluation'].isin(['no_evaluation', 'not_specified'])).sum() / len(vt_df)
        if no_eval_rate > 0.5:
            recommendations.append("- **Increase empirical evaluations**: Over 50% of virtual tutors lack proper evaluation")

    # Check for domain diversity
    if 'subject_domain' in vt_df.columns:
        unique_domains = vt_df['subject_domain'].nunique()
        if unique_domains < 5:
            recommendations.append("- **Expand domain coverage**: Virtual tutors are concentrated in few subject areas")

    # Check for privacy concerns
    if 'privacy_protection' in vt_df.columns:
        privacy_addressed = (vt_df['privacy_protection'] != 'not_mentioned').sum() / len(vt_df)
        if privacy_addressed < 0.3:
            recommendations.append("- **Address privacy concerns**: Less than 30% of papers discuss data protection")

    for rec in recommendations:
        st.write(rec)

    # Export options
    st.write("### Export Options")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Full dataset export
        csv = vt_df.to_csv(index=False)
        st.download_button(
            "📊 Export Full VT Dataset",
            csv,
            "virtual_tutors_full.csv",
            "text/csv"
        )

    with col2:
        # Summary statistics export
        summary_stats = {
            'Total Papers': total_papers,
            'Assessed Papers': assessed_papers,
            'Virtual Tutor Papers': vt_papers,
            'Implementation Papers': impl_papers,
            'Papers with Evaluation': len(vt_df[~vt_df['empirical_evaluation'].isin(['no_evaluation', 'not_specified'])]),
            'Papers with RAG': len(vt_df[vt_df['uses_rag'] == 'yes']),
            'Papers with Collaboration': len(vt_df[vt_df['supports_collaboration'] == 'yes'])
        }
        summary_df = pd.DataFrame(list(summary_stats.items()), columns=['Metric', 'Count'])
        csv = summary_df.to_csv(index=False)
        st.download_button(
            "📈 Export Summary Stats",
            csv,
            "summary_statistics.csv",
            "text/csv"
        )

    with col3:
        # Generate a text report
        report_text = f"""
SYSTEMATIC LITERATURE REVIEW - VIRTUAL TUTORS IN HIGHER EDUCATION
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

OVERVIEW
========
Total Papers Analyzed: {total_papers}
Papers Assessed: {assessed_papers}
Virtual Tutor Papers: {vt_papers}
Implementation Papers: {impl_papers}

KEY FINDINGS
============
{summary_text}

RECOMMENDATIONS
===============
{"".join(recommendations)}

This report was automatically generated from the systematic literature review database.
        """
        st.download_button(
            "📄 Export Text Report",
            report_text,
            "slr_report.txt",
            "text/plain"
        )


def main():
    load_dotenv(find_dotenv())
    st.set_page_config(
        page_title="Virtual Tutor Literature Dashboard",
        initial_sidebar_state="expanded",
        layout="wide"
    )

    # Initialize the db
    setup_database()

    with st.sidebar:
        st.header("Data Import Actions")

        if st.button("Import Citations", help="Import citations from configured sources"):
            with st.spinner("Importing citations..."):
                import_citations()
                st.success("Citations imported!")

        if st.button("Process Papers", help="Process PDFs in 'papers' directory"):
            with st.spinner("Processing papers..."):
                process_papers()
                st.success("Papers processed!")

        st.divider()

        # NEW: Add arXiv import section
        st.subheader("Import arXiv Papers")
        arxiv_dir = st.text_input(
            "arXiv PDF Directory",
            value="arxiv_papers",
            help="Directory containing arXiv PDFs to import"
        )

        if st.button("Import arXiv PDFs",
                     help="Import PDFs and create database entries automatically"):
            if arxiv_dir and Path(arxiv_dir).exists():
                pdf_files = list(Path(arxiv_dir).glob('*.pdf'))
                pdf_count = len(pdf_files)
                if pdf_count > 0:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    with st.spinner(f"Importing {pdf_count} arXiv papers..."):
                        try:
                            import_arxiv_papers(arxiv_dir)
                            st.success(f"Completed importing arXiv papers!")

                            # Show summary
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                           SELECT COUNT(*) FROM papers
                                           WHERE publication_source = 'arxiv_auto_import'
                                           """)
                            imported_count = cursor.fetchone()[0]
                            st.info(f"Total arXiv papers in database: {imported_count}")

                        except Exception as e:
                            st.error(f"Error during import: {str(e)}")
                            st.info("If you see 'NOT NULL constraint failed', please run migrate_database.py first")
                else:
                    st.warning(f"No PDF files found in '{arxiv_dir}'")
            else:
                st.error(f"Directory '{arxiv_dir}' does not exist!")

    try:
        papers_df = load_data_with_lists()
    except sqlite3.OperationalError:
        st.error("Please import citations and process papers first!")
        st.stop()

    # Print debug info about initial data
    print("\nInitial data load:")
    print(f"Total papers: {len(papers_df)}")
    print("\nColumns present:", papers_df.columns.tolist())
    print("\nAssessment status distribution:")
    print(papers_df['assessment_status'].value_counts(dropna=False))

    # Create filters that will be used across tabs
    filters = create_filters(papers_df)

    # Create tabs
    papers_tab, assessments_tab, keywords_tab, analysis_tab, papers_view_tab, add_paper_tab = st.tabs([
        "Papers", "Aggregated Assessments", "Keyword Analysis", "📊 Analysis", "Paper Assessments", "Add Paper"
    ])

    with papers_tab:
        filtered_df = apply_filters(papers_df, filters)
        display_papers_tab(filtered_df)

    with assessments_tab:
        display_assessments_tab(papers_df, filters)

    with keywords_tab:
        display_keywords_tab(papers_df, filters)

    with papers_view_tab:
        papers_view(filters)

    with add_paper_tab:
        add_paper()

    with analysis_tab:
        display_analysis_tab(papers_df, filters)


if __name__ == "__main__":
    main()
