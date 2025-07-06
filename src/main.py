"""
This is the main script for the literature management application.
It provides a streamlit interface to import citations, process papers, and view the database.
"""
import streamlit as st
import pandas as pd
import sqlite3
import json
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from dotenv import find_dotenv, load_dotenv
from process_papers import PdfProcessor
from pathlib import Path
from import_citations import CitationProcessor
from view_paper import papers_view


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


def setup_database_with_connection(conn):
    """Setup database using existing connection"""
    cursor = conn.cursor()

    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")

    # Main table for papers
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS papers (
                                                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                         doi TEXT UNIQUE NOT NULL,
                                                         title TEXT,
                                                         publication_year INTEGER,
                                                         authors TEXT,
                                                         venue TEXT,
                                                         volume TEXT,
                                                         publication_type TEXT,
                                                         publication_source TEXT,
                                                         processed BOOLEAN DEFAULT 0,
                                                         file_path TEXT DEFAULT NULL
                   )
                   """)

    # Table for virtual tutor assessments
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS virtual_tutor_assessments (
                                                                            paper_id INTEGER PRIMARY KEY,
                       -- Phase 1
                                                                            is_virtual_tutor BOOLEAN,
                                                                            is_implementation BOOLEAN,
                       -- Phase 2
                                                                            deployment_status TEXT,
                                                                            llm_model TEXT,
                                                                            uses_rag TEXT,
                                                                            primary_function TEXT,
                                                                            subject_domain TEXT,
                                                                            generates_assessments TEXT,
                       -- Phase 3
                                                                            publication_type TEXT,
                                                                            availability TEXT,
                       -- Phase 4
                                                                            lms_integration TEXT,
                       -- Phase 5
                                                                            personalization TEXT,
                                                                            supports_collaboration TEXT,
                       -- Phase 6
                                                                            empirical_evaluation TEXT,
                                                                            sample_size TEXT,
                                                                            evaluation_duration TEXT,
                       -- Phase 7
                                                                            institution_type TEXT,
                                                                            development_approach TEXT,
                                                                            language_support TEXT,
                       -- Phase 8
                                                                            privacy_protection TEXT,
                                                                            cost_requirements TEXT,
                                                                            reference_architecture TEXT,
                       -- Metadata
                                                                            assessment_date TIMESTAMP,
                                                                            FOREIGN KEY (paper_id) REFERENCES papers (id)
                       )
                   """)

    # Table for keywords
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS keywords (
                                                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                           keyword TEXT UNIQUE
                   )
                   """)

    # Relationship table for keywords and papers
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS rel_keywords_papers (
                                                                      paper_id INTEGER,
                                                                      keyword_id INTEGER,
                                                                      FOREIGN KEY (paper_id) REFERENCES papers (id),
                       FOREIGN KEY (keyword_id) REFERENCES keywords (id)
                       )
                   """)

    # Add normalized tables for list fields
    list_tables = [
        """
        CREATE TABLE IF NOT EXISTS assessment_architecture_components (
                                                                          paper_id INTEGER,
                                                                          component TEXT,
                                                                          PRIMARY KEY (paper_id, component),
            FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS assessment_interaction_modalities (
                                                                         paper_id INTEGER,
                                                                         modality TEXT,
                                                                         PRIMARY KEY (paper_id, modality),
            FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS assessment_analytics_features (
                                                                     paper_id INTEGER,
                                                                     feature TEXT,
                                                                     PRIMARY KEY (paper_id, feature),
            FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS assessment_pedagogical_features (
                                                                       paper_id INTEGER,
                                                                       feature TEXT,
                                                                       PRIMARY KEY (paper_id, feature),
            FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS assessment_collaboration_types (
                                                                      paper_id INTEGER,
                                                                      collaboration_type TEXT,
                                                                      PRIMARY KEY (paper_id, collaboration_type),
            FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS assessment_aspects_evaluated (
                                                                    paper_id INTEGER,
                                                                    aspect TEXT,
                                                                    PRIMARY KEY (paper_id, aspect),
            FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
            )
        """
    ]

    for table_sql in list_tables:
        cursor.execute(table_sql)

    conn.commit()


@st.cache_resource
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
               a.llm_model,
               a.primary_function,
               a.empirical_evaluation,
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
    setup_database_with_connection(conn)
    conn.close()


def import_citations():
    # Configure base path for search results
    search_dir = Path('search_results')

    # Configure files with relative paths
    file_config = {
        'bibtex': [
            search_dir / 'acm.bib',
            search_dir / 'ScienceDirect_1.bib',
            search_dir / 'ScienceDirect_2.bib',
            search_dir / 'wiley_1.bib',
            search_dir / 'wiley_2.bib'
        ],
        'ieee': [search_dir / 'ieee.csv'],
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
        'publication_type', 'publication_source', 'doi'
    ]
    st.dataframe(
        papers_df[display_cols],
        hide_index=True,
        use_container_width=True
    )


def add_paper():
    st.title("Add Paper")

    # Form for paper details
    with st.form("paper_form"):
        doi = st.text_input("DOI*", help="Digital Object Identifier (required)")
        title = st.text_input("Title*", help="Paper title (required)")
        year = st.number_input("Publication Year*", min_value=1900, max_value=2100, value=2024)
        authors = st.text_input("Authors*", help="Comma-separated list of authors")
        venue = st.text_input("Venue", help="Journal or conference name")
        volume = st.text_input("Volume")
        publication_type = st.text_input("Publication Type")
        publication_source = st.text_input("Publication Source", help="Where this paper was found")

        submitted = st.form_submit_button("Add Paper")

        if submitted:
            if not all([doi, title, authors]):
                st.error("Please fill in all required fields (marked with *)")
                return

            conn = get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                               INSERT INTO papers
                               (doi, title, publication_year, authors, venue, volume, publication_type, publication_source)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                               """, (doi, title, year, authors, venue, volume, publication_type, publication_source))

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
        if st.button("Import Citations"):
            with st.spinner("Importing citations..."):
                import_citations()

        if st.button("Process Papers"):
            with st.spinner("Processing papers..."):
                process_papers()

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
    papers_tab, assessments_tab, keywords_tab, papers_view_tab, add_paper_tab = st.tabs([
        "Papers", "Aggregated Assessments", "Keyword Analysis", "Paper Assessments", "Add Paper"
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


if __name__ == "__main__":
    main()
