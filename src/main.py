"""
Literature Management System - Streamlit Dashboard

A general-purpose Systematic Literature Review (SLR) tool.
Supports multiple projects with configurable questions and content matrix.
"""
import streamlit as st
import pandas as pd
import sqlite3
import json
import logging
import os
import numpy as np
import plotly.express as px
from dotenv import find_dotenv, load_dotenv
from pathlib import Path
from import_citations import CitationProcessor
from models import ProjectConfig, AnswerType
from assessment import AssessmentRunner, get_matrix_data, clear_matrix


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@st.cache_resource
def get_connection():
    """Get cached SQLite database connection."""
    conn = sqlite3.connect('literature.db', check_same_thread=False)

    # Check if tables exist
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sources'")
    if cursor.fetchone() is None:
        setup_database_with_connection(conn)

    return conn


def setup_database_with_connection(conn, schema_path='src/schema.sql'):
    """Initialize database using the provided connection and schema file."""
    cursor = conn.cursor()

    try:
        if not Path(schema_path).exists():
            st.error(f"Schema file '{schema_path}' not found!")
            raise FileNotFoundError(f"Schema file '{schema_path}' not found")

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        conn.executescript(schema_sql)
        conn.commit()
        logger.info(f"Database initialized successfully using {schema_path}")

    except FileNotFoundError as e:
        logger.error(f"Schema file error: {e}")
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error during schema creation: {e}")
        raise


def setup_database(db_path: str = 'literature.db'):
    """Initialize the database from schema file if needed."""
    schema_path = Path('src/schema.sql')

    if not schema_path.exists():
        st.error("Schema file not found!")
        st.info("Please make sure src/schema.sql exists")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sources'")
        if cursor.fetchone() is None:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
            conn.commit()
            logger.info("Database initialized successfully")

        conn.close()

    except Exception as e:
        st.error(f"Database initialization error: {e}")
        raise


# Project management functions

def load_projects():
    """Load all projects from database."""
    conn = get_connection()
    query = "SELECT id, name, topic, description, config, created_at FROM projects ORDER BY name"
    return pd.read_sql_query(query, conn)


def get_project(project_id: int):
    """Get a single project by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, topic, description, config, created_at FROM projects WHERE id = ?",
        (project_id,)
    )
    row = cursor.fetchone()
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'topic': row[2],
            'description': row[3],
            'config': row[4],
            'created_at': row[5]
        }
    return None


def create_project(name: str, topic: str = '', description: str = '', config: str = '{}'):
    """Create a new project."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO projects (name, topic, description, config) VALUES (?, ?, ?, ?)",
        (name, topic, description, config)
    )
    conn.commit()
    return cursor.lastrowid


def update_project(project_id: int, name: str, topic: str, description: str, config: str):
    """Update an existing project."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE projects SET name = ?, topic = ?, description = ?, config = ? WHERE id = ?",
        (name, topic, description, config, project_id)
    )
    conn.commit()


def delete_project(project_id: int):
    """Delete a project and its associations."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()


def duplicate_project(project_id: int, new_name: str) -> int:
    """Duplicate a project with a new name (config only, not sources)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get original project
    cursor.execute(
        "SELECT topic, description, config FROM projects WHERE id = ?",
        (project_id,)
    )
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Project {project_id} not found")

    topic, description, config = row

    # Create new project
    cursor.execute(
        "INSERT INTO projects (name, topic, description, config) VALUES (?, ?, ?, ?)",
        (new_name, topic, description, config)
    )
    conn.commit()
    return cursor.lastrowid


# Source management functions

def load_sources(project_id: int = None):
    """Load sources, optionally filtered by project."""
    conn = get_connection()

    if project_id:
        query = """
            SELECT
                s.id,
                s.identifier,
                s.identifier_type,
                s.title,
                s.authors,
                s.year,
                s.publication,
                s.source_type,
                s.import_source,
                s.file_path
            FROM sources s
            JOIN project_sources ps ON s.id = ps.source_id
            WHERE ps.project_id = ?
            ORDER BY s.year DESC, s.title
        """
        return pd.read_sql_query(query, conn, params=(project_id,))
    else:
        query = """
            SELECT
                id,
                identifier,
                identifier_type,
                title,
                authors,
                year,
                publication,
                source_type,
                import_source,
                file_path
            FROM sources
            ORDER BY year DESC, title
        """
        return pd.read_sql_query(query, conn)


def load_all_sources():
    """Load all sources (global view)."""
    return load_sources(project_id=None)


def add_source_to_project(source_id: int, project_id: int):
    """Link an existing source to a project."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO project_sources (project_id, source_id) VALUES (?, ?)",
            (project_id, source_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error adding source to project: {e}")
        return False


def remove_source_from_project(source_id: int, project_id: int):
    """Remove a source from a project (doesn't delete the source)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM project_sources WHERE project_id = ? AND source_id = ?",
        (project_id, source_id)
    )
    conn.commit()


def get_source_details(source_id: int) -> dict:
    """Get full details for a source including keywords."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, identifier, identifier_type, title, authors, year,
               abstract, publication, source_type, import_source, content, metadata
        FROM sources WHERE id = ?
    """, (source_id,))
    row = cursor.fetchone()

    if not row:
        return None

    # Get keywords
    cursor.execute("""
        SELECT k.keyword FROM keywords k
        JOIN rel_keywords_sources r ON k.id = r.keyword_id
        WHERE r.source_id = ?
    """, (source_id,))
    keywords = [r[0] for r in cursor.fetchall()]

    return {
        'id': row[0],
        'identifier': row[1],
        'identifier_type': row[2],
        'title': row[3],
        'authors': row[4],
        'year': row[5],
        'abstract': row[6],
        'publication': row[7],
        'source_type': row[8],
        'import_source': row[9],
        'content': row[10],
        'metadata': row[11],
        'keywords': keywords
    }


def delete_source(source_id: int):
    """Delete a source and all its associations."""
    conn = get_connection()
    cursor = conn.cursor()
    # Delete from junction tables first
    cursor.execute("DELETE FROM project_sources WHERE source_id = ?", (source_id,))
    cursor.execute("DELETE FROM rel_keywords_sources WHERE source_id = ?", (source_id,))
    cursor.execute("DELETE FROM content_matrix WHERE source_id = ?", (source_id,))
    # Delete the source
    cursor.execute("DELETE FROM sources WHERE id = ?", (source_id,))
    conn.commit()


def bulk_add_sources_to_project(source_ids: list, project_id: int):
    """Add multiple sources to a project."""
    conn = get_connection()
    cursor = conn.cursor()
    for source_id in source_ids:
        cursor.execute(
            "INSERT OR IGNORE INTO project_sources (project_id, source_id) VALUES (?, ?)",
            (project_id, source_id)
        )
    conn.commit()


def bulk_remove_sources_from_project(source_ids: list, project_id: int):
    """Remove multiple sources from a project."""
    conn = get_connection()
    cursor = conn.cursor()
    for source_id in source_ids:
        cursor.execute(
            "DELETE FROM project_sources WHERE project_id = ? AND source_id = ?",
            (project_id, source_id)
        )
    conn.commit()


def import_citations(project_id: int = None):
    """Import citations from configured sources."""
    search_dir = Path('search_results')

    file_config = {
        'ieee': [search_dir / 'ieee.csv'],
        'bibtex': [
            search_dir / 'acm.bib',
            search_dir / 'ScienceDirect_1.bib',
            search_dir / 'ScienceDirect_2.bib',
        ],
        'springer': [
            search_dir / 'SpringerLink_1.csv',
            search_dir / 'SpringerLink_2.csv'
        ],
    }

    processor = CitationProcessor(project_id=project_id)
    processor.process_files(file_config)


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles NumPy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


# Keyword functions

def load_keyword_data(project_id: int = None):
    """Load keyword frequency data, optionally scoped to a project."""
    conn = get_connection()

    if project_id:
        query = """
            SELECT
                k.keyword,
                COUNT(DISTINCT r.source_id) as source_count
            FROM keywords k
            JOIN rel_keywords_sources r ON k.id = r.keyword_id
            JOIN project_sources ps ON r.source_id = ps.source_id
            WHERE ps.project_id = ?
            GROUP BY k.id, k.keyword
            HAVING source_count > 0
            ORDER BY source_count DESC
        """
        return pd.read_sql_query(query, conn, params=(project_id,))
    else:
        query = """
            SELECT
                k.keyword,
                COUNT(r.source_id) as source_count
            FROM keywords k
            LEFT JOIN rel_keywords_sources r ON k.id = r.keyword_id
            GROUP BY k.id, k.keyword
            HAVING source_count > 0
            ORDER BY source_count DESC
        """
        return pd.read_sql_query(query, conn)


# UI Components

def display_project_selector():
    """Display project selector in sidebar and return selected project ID."""
    projects_df = load_projects()

    if projects_df.empty:
        st.sidebar.info("No projects yet. Create one in the Projects tab.")
        return None

    # Build options list
    options = [{"id": None, "label": "All Sources (Global)"}]
    for _, row in projects_df.iterrows():
        options.append({"id": row['id'], "label": row['name']})

    # Get current selection from session state
    current_idx = 0
    if 'selected_project_id' in st.session_state:
        for i, opt in enumerate(options):
            if opt['id'] == st.session_state.selected_project_id:
                current_idx = i
                break

    selected = st.sidebar.selectbox(
        "Project",
        options,
        index=current_idx,
        format_func=lambda x: x['label']
    )

    st.session_state.selected_project_id = selected['id']
    return selected['id']


def display_projects_tab():
    """Display the projects management tab."""
    st.title("Projects")

    # Create new project form
    st.subheader("Create New Project")
    with st.form("create_project_form"):
        name = st.text_input("Project Name*", help="Required")
        topic = st.text_input("Topic", help="Brief topic description")
        description = st.text_area("Description", help="Detailed project description")

        st.markdown("**Configuration (JSON)**")
        config_help = """Define questions for the content matrix. Example:
```json
{
  "questions": [
    {"key": "uses_llm", "text": "Does it use LLM?", "answer_type": "boolean"},
    {"key": "method", "text": "What method is used?", "answer_type": "text"}
  ]
}
```"""
        st.caption(config_help)
        config = st.text_area("Config JSON", value="{}", height=150)

        submitted = st.form_submit_button("Create Project")

        if submitted:
            if not name:
                st.error("Project name is required")
            else:
                try:
                    json.loads(config)  # Validate JSON
                    project_id = create_project(name, topic, description, config)
                    st.success(f"Created project: {name}")
                    st.session_state.selected_project_id = project_id
                    st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON configuration: {e}")

    st.divider()

    # List existing projects
    st.subheader("Existing Projects")
    projects_df = load_projects()

    if projects_df.empty:
        st.info("No projects created yet.")
        return

    for _, row in projects_df.iterrows():
        project_id = row['id']
        edit_key = f"editing_project_{project_id}"

        with st.expander(f"**{row['name']}** - {row['topic'] or 'No topic'}"):
            # Check if we're editing this project
            if st.session_state.get(edit_key, False):
                # Edit form
                with st.form(f"edit_form_{project_id}"):
                    st.subheader("Edit Project")
                    edit_name = st.text_input("Name", value=row['name'])
                    edit_topic = st.text_input("Topic", value=row['topic'] or '')
                    edit_desc = st.text_area("Description", value=row['description'] or '')
                    edit_config = st.text_area("Config JSON", value=row['config'] or '{}', height=200)

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Save"):
                            try:
                                json.loads(edit_config)  # Validate JSON
                                update_project(project_id, edit_name, edit_topic, edit_desc, edit_config)
                                st.session_state[edit_key] = False
                                st.success("Project updated!")
                                st.rerun()
                            except json.JSONDecodeError as e:
                                st.error(f"Invalid JSON: {e}")
                    with col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state[edit_key] = False
                            st.rerun()
            else:
                # Display mode
                st.write(f"**Description:** {row['description'] or 'None'}")
                st.write(f"**Created:** {row['created_at']}")

                # Show source count
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM project_sources WHERE project_id = ?",
                    (project_id,)
                )
                source_count = cursor.fetchone()[0]
                st.write(f"**Sources:** {source_count}")

                # Config display
                if row['config']:
                    try:
                        config_data = json.loads(row['config'])
                        if config_data:
                            st.json(config_data)
                    except json.JSONDecodeError:
                        st.code(row['config'])

                # Action buttons
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("Select", key=f"select_{project_id}"):
                        st.session_state.selected_project_id = project_id
                        st.rerun()
                with col2:
                    if st.button("Edit", key=f"edit_{project_id}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                with col3:
                    if st.button("Duplicate", key=f"dup_{project_id}"):
                        new_id = duplicate_project(project_id, f"{row['name']} (copy)")
                        st.success(f"Created copy: {row['name']} (copy)")
                        st.rerun()
                with col4:
                    if st.button("Delete", key=f"delete_{project_id}", type="secondary"):
                        delete_project(project_id)
                        if st.session_state.get('selected_project_id') == project_id:
                            st.session_state.selected_project_id = None
                        st.rerun()


def display_sources_tab(project_id: int = None):
    """Display the sources tab with statistics and data table."""
    st.title("Sources")

    # Show which project we're viewing
    if project_id:
        project = get_project(project_id)
        if project:
            st.caption(f"Viewing sources for project: **{project['name']}**")
    else:
        st.caption("Viewing all sources (global)")

    sources_df = load_sources(project_id)

    if sources_df.empty:
        st.warning("No sources found. Import some citations first.")
        return

    # Basic statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sources", len(sources_df))
    with col2:
        years = sources_df['year'].dropna()
        if not years.empty:
            st.metric("Year Range", f"{int(years.min())} - {int(years.max())}")
    with col3:
        imports = sources_df['import_source'].nunique()
        st.metric("Import Sources", imports)

    st.divider()

    # Publications by year
    if 'year' in sources_df.columns:
        year_counts = sources_df['year'].value_counts().sort_index()
        if not year_counts.empty:
            fig = px.bar(
                x=year_counts.index,
                y=year_counts.values,
                labels={'x': 'Year', 'y': 'Number of Sources'},
                title="Publications by Year"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Data table
    st.subheader("Sources")

    # Search filter
    search = st.text_input("Search sources", placeholder="Filter by title, authors...")
    if search:
        mask = (
            sources_df['title'].str.contains(search, case=False, na=False) |
            sources_df['authors'].str.contains(search, case=False, na=False)
        )
        display_df = sources_df[mask]
    else:
        display_df = sources_df

    # Bulk selection
    st.markdown("**Select sources for bulk operations:**")

    # Initialize selection state
    if 'selected_sources' not in st.session_state:
        st.session_state.selected_sources = set()

    # Select all / deselect all
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Select All"):
            st.session_state.selected_sources = set(display_df['id'].tolist())
            st.rerun()
    with col2:
        if st.button("Deselect All"):
            st.session_state.selected_sources = set()
            st.rerun()

    # Display sources with checkboxes and detail view
    for _, row in display_df.iterrows():
        source_id = row['id']
        col1, col2 = st.columns([0.05, 0.95])

        with col1:
            selected = st.checkbox(
                "",
                value=source_id in st.session_state.selected_sources,
                key=f"select_source_{source_id}",
                label_visibility="collapsed"
            )
            if selected and source_id not in st.session_state.selected_sources:
                st.session_state.selected_sources.add(source_id)
            elif not selected and source_id in st.session_state.selected_sources:
                st.session_state.selected_sources.discard(source_id)

        with col2:
            title = row['title'][:70] + '...' if len(row.get('title') or '') > 70 else row.get('title', 'Untitled')
            with st.expander(f"**{title}** ({row.get('year', 'N/A')})"):
                # Get full details
                details = get_source_details(source_id)
                if details:
                    st.write(f"**Authors:** {details.get('authors') or 'N/A'}")
                    st.write(f"**Publication:** {details.get('publication') or 'N/A'}")
                    st.write(f"**Type:** {details.get('source_type') or 'N/A'}")
                    st.write(f"**Source:** {details.get('import_source') or 'N/A'}")

                    if details.get('identifier'):
                        id_type = details.get('identifier_type', 'unknown')
                        if id_type == 'doi':
                            st.write(f"**DOI:** [{details['identifier']}](https://doi.org/{details['identifier']})")
                        else:
                            st.write(f"**ID:** {details['identifier']} ({id_type})")

                    if details.get('keywords'):
                        st.write(f"**Keywords:** {', '.join(details['keywords'])}")

                    if details.get('abstract'):
                        st.write("**Abstract:**")
                        st.markdown(details['abstract'])

                    if details.get('content'):
                        with st.expander("Full Content"):
                            st.text(details['content'][:5000] + ('...' if len(details['content']) > 5000 else ''))

    # Bulk operations
    selected_count = len(st.session_state.selected_sources)
    if selected_count > 0:
        st.divider()
        st.subheader(f"Bulk Operations ({selected_count} selected)")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Add to project (for global view)
            if not project_id:
                projects_df = load_projects()
                if not projects_df.empty:
                    target_project = st.selectbox(
                        "Add to project:",
                        options=projects_df['id'].tolist(),
                        format_func=lambda x: projects_df[projects_df['id'] == x]['name'].iloc[0]
                    )
                    if st.button("Add to Project"):
                        bulk_add_sources_to_project(list(st.session_state.selected_sources), target_project)
                        st.success(f"Added {selected_count} sources to project")
                        st.rerun()

        with col2:
            # Remove from project (if viewing a project)
            if project_id:
                if st.button("Remove from Project"):
                    bulk_remove_sources_from_project(list(st.session_state.selected_sources), project_id)
                    st.session_state.selected_sources = set()
                    st.success(f"Removed {selected_count} sources from project")
                    st.rerun()

        with col3:
            # Delete permanently
            if st.button("Delete Selected", type="secondary"):
                st.session_state.confirm_delete_sources = True

            if st.session_state.get('confirm_delete_sources', False):
                st.warning(f"Are you sure you want to permanently delete {selected_count} sources?")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Yes, Delete"):
                        for sid in list(st.session_state.selected_sources):
                            delete_source(sid)
                        st.session_state.selected_sources = set()
                        st.session_state.confirm_delete_sources = False
                        st.success(f"Deleted {selected_count} sources")
                        st.rerun()
                with col_b:
                    if st.button("Cancel"):
                        st.session_state.confirm_delete_sources = False
                        st.rerun()

    st.divider()

    # Export
    if st.button("Export to CSV"):
        csv = sources_df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "sources.csv",
            "text/csv"
        )


def display_add_source_tab(project_id: int = None):
    """Form to manually add a source."""
    st.title("Add Source")

    if project_id:
        project = get_project(project_id)
        if project:
            st.caption(f"Adding to project: **{project['name']}**")

    with st.form("add_source_form"):
        title = st.text_input("Title*", help="Required")
        authors = st.text_input("Authors", help="Comma-separated")
        year = st.number_input("Publication Year", min_value=1900, max_value=2100, value=2024)
        publication = st.text_input("Publication/Venue")
        doi = st.text_input("DOI")
        source_type = st.selectbox(
            "Source Type",
            ["journal", "conference", "preprint", "book", "thesis", "web", "other"]
        )

        submitted = st.form_submit_button("Add Source")

        if submitted:
            if not title:
                st.error("Title is required")
                return

            conn = get_connection()
            cursor = conn.cursor()

            try:
                # Determine identifier
                if doi:
                    identifier = doi.strip()
                    identifier_type = 'doi'
                else:
                    import hashlib
                    content = f"{title.lower().strip()}|{authors.lower().strip()}|{year}"
                    identifier = hashlib.sha256(content.encode()).hexdigest()[:16]
                    identifier_type = 'hash'

                cursor.execute("""
                    INSERT INTO sources (identifier, identifier_type, title, authors, year,
                                        publication, source_type, import_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (identifier, identifier_type, title, authors, year, publication,
                      source_type, 'manual'))
                conn.commit()

                source_id = cursor.lastrowid

                # Link to project if one is selected
                if project_id:
                    cursor.execute(
                        "INSERT INTO project_sources (project_id, source_id) VALUES (?, ?)",
                        (project_id, source_id)
                    )
                    conn.commit()

                st.success(f"Added: {title}")

            except sqlite3.IntegrityError:
                st.error("A source with this identifier already exists")
            except Exception as e:
                st.error(f"Error adding source: {e}")


def display_content_matrix_tab(project_id: int = None):
    """Display the content matrix tab."""
    st.title("Content Matrix")

    if not project_id:
        st.warning("Select a project to view its content matrix.")
        return

    project = get_project(project_id)
    if not project:
        st.error("Project not found.")
        return

    st.caption(f"Content matrix for project: **{project['name']}**")

    # Parse project config
    try:
        config = ProjectConfig.model_validate_json(project['config'] or '{}')
    except Exception as e:
        st.error(f"Invalid project configuration: {e}")
        st.info("Go to the Projects tab to fix the configuration.")
        return

    if not config.questions:
        st.warning("No questions configured for this project.")
        st.info("Go to the Projects tab to add questions to the configuration.")
        return

    # Show assessment controls
    st.subheader("Assessment")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        # Check if OPENAI_API_KEY is set
        api_key_set = bool(os.getenv('OPENAI_API_KEY'))
        if not api_key_set:
            st.warning("OPENAI_API_KEY not set. Assessment requires an API key.")

    with col2:
        run_assessment = st.button(
            "Run Assessment",
            disabled=not api_key_set,
            help="Assess all sources against configured questions"
        )

    with col3:
        if st.button("Clear Matrix", type="secondary", help="Delete all assessment results"):
            clear_matrix(get_connection(), project_id)
            st.success("Matrix cleared!")
            st.rerun()

    # Run assessment if requested
    if run_assessment:
        _run_assessment_with_progress(project_id, config)
        st.rerun()

    st.divider()

    # Load and display matrix data
    matrix_data = get_matrix_data(get_connection(), project_id)

    if not matrix_data['sources']:
        st.info("No sources in this project. Add sources first.")
        return

    # Build DataFrame for display
    df_data = []
    for source in matrix_data['sources']:
        row = {
            'Title': source['title'][:60] + '...' if len(source.get('title', '') or '') > 60 else source.get('title', ''),
            'Year': source.get('year'),
        }

        # Add question columns
        source_matrix = matrix_data['matrix'].get(source['id'], {})
        for q in config.questions:
            cell = source_matrix.get(q.key, {})
            answer = cell.get('answer', '')
            confidence = cell.get('confidence', '')

            if answer:
                # Format with confidence indicator
                conf_emoji = {'high': '', 'medium': '', 'low': ''}.get(confidence, '')
                row[q.key] = f"{answer}{conf_emoji}"
            else:
                row[q.key] = ''

        df_data.append(row)

    if df_data:
        df = pd.DataFrame(df_data)

        # Stats
        total_cells = len(matrix_data['sources']) * len(config.questions)
        filled_cells = sum(
            1 for s in matrix_data['sources']
            for q in config.questions
            if matrix_data['matrix'].get(s['id'], {}).get(q.key, {}).get('answer')
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sources", len(matrix_data['sources']))
        with col2:
            st.metric("Questions", len(config.questions))
        with col3:
            pct = (filled_cells / total_cells * 100) if total_cells > 0 else 0
            st.metric("Completion", f"{filled_cells}/{total_cells} ({pct:.0f}%)")

        # Visualizations
        if filled_cells > 0:
            st.subheader("Analysis")

            # Confidence distribution across all answers
            confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
            for source in matrix_data['sources']:
                source_matrix = matrix_data['matrix'].get(source['id'], {})
                for q in config.questions:
                    cell = source_matrix.get(q.key, {})
                    conf = cell.get('confidence')
                    if conf in confidence_counts:
                        confidence_counts[conf] += 1

            if sum(confidence_counts.values()) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    conf_df = pd.DataFrame([
                        {'Confidence': k.title(), 'Count': v}
                        for k, v in confidence_counts.items()
                    ])
                    fig = px.pie(
                        conf_df,
                        values='Count',
                        names='Confidence',
                        title='Answer Confidence Distribution',
                        color='Confidence',
                        color_discrete_map={'High': '#2ecc71', 'Medium': '#f39c12', 'Low': '#e74c3c'}
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Answer distributions per question
                with col2:
                    # Build answer counts per question
                    question_data = []
                    for q in config.questions:
                        answer_counts = {}
                        for source in matrix_data['sources']:
                            source_matrix = matrix_data['matrix'].get(source['id'], {})
                            cell = source_matrix.get(q.key, {})
                            answer = cell.get('answer')
                            if answer:
                                # Truncate long answers for display
                                display_answer = str(answer)[:30]
                                answer_counts[display_answer] = answer_counts.get(display_answer, 0) + 1
                        for ans, count in answer_counts.items():
                            question_data.append({
                                'Question': q.key,
                                'Answer': ans,
                                'Count': count
                            })

                    if question_data:
                        q_df = pd.DataFrame(question_data)
                        # Show distribution for first question with enum/boolean type
                        for q in config.questions:
                            if q.answer_type.value in ('boolean', 'enum'):
                                subset = q_df[q_df['Question'] == q.key]
                                if not subset.empty:
                                    fig = px.bar(
                                        subset,
                                        x='Answer',
                                        y='Count',
                                        title=f'Answers: {q.key}'
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                    break

            # Completion heatmap
            st.markdown("**Completion Matrix**")
            heatmap_data = []
            for source in matrix_data['sources']:
                row = {'Source': source['title'][:40] if source.get('title') else f"ID {source['id']}"}
                source_matrix = matrix_data['matrix'].get(source['id'], {})
                for q in config.questions:
                    cell = source_matrix.get(q.key, {})
                    row[q.key] = 1 if cell.get('answer') else 0
                heatmap_data.append(row)

            if heatmap_data:
                heatmap_df = pd.DataFrame(heatmap_data)
                if len(config.questions) > 0 and len(heatmap_df) > 0:
                    # Create heatmap with question keys as columns
                    question_keys = [q.key for q in config.questions]
                    heatmap_values = heatmap_df[question_keys].values

                    fig = px.imshow(
                        heatmap_values,
                        labels=dict(x="Question", y="Source", color="Completed"),
                        x=question_keys,
                        y=heatmap_df['Source'].tolist(),
                        color_continuous_scale=['#f8f9fa', '#2ecc71'],
                        aspect='auto'
                    )
                    fig.update_layout(title='Assessment Completion (green = answered)')
                    st.plotly_chart(fig, use_container_width=True)

        # Display matrix
        st.subheader("Matrix")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Export options
        st.subheader("Export")
        col1, col2 = st.columns(2)

        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"content_matrix_{project['name']}.csv",
                "text/csv"
            )

        with col2:
            # Full export with all details
            full_export = _build_full_export(matrix_data, config)
            st.download_button(
                "Download Full JSON",
                json.dumps(full_export, indent=2, cls=NumpyEncoder),
                f"content_matrix_{project['name']}.json",
                "application/json"
            )
    else:
        st.info("No assessment data yet. Run assessment to populate the matrix.")


def _run_assessment_with_progress(project_id: int, config: ProjectConfig):
    """Run assessment with a progress bar."""
    from agent import create_agent

    try:
        agent = create_agent(
            model=config.model,
            system_prompt=config.system_prompt
        )
    except Exception as e:
        st.error(f"Failed to create agent: {e}")
        return

    runner = AssessmentRunner(
        conn=get_connection(),
        project_id=project_id,
        config=config,
        agent=agent
    )

    # Get counts for progress bar
    sources = runner.get_sources()
    pending = list(runner.get_pending_assessments(sources, config.questions))

    if not pending:
        st.info("All sources have already been assessed.")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    completed = 0
    total = len(pending)

    def update_progress(progress):
        nonlocal completed
        completed = progress.completed_assessments
        pct = completed / total if total > 0 else 1.0
        progress_bar.progress(pct)
        if progress.current_source:
            status_text.text(f"Assessing: {progress.current_source[:40]}... ({progress.current_question})")
        else:
            status_text.text("Assessment complete!")

    with st.spinner(f"Running assessment on {total} pending items..."):
        result = runner.run(progress_callback=update_progress)

    progress_bar.progress(1.0)
    st.success(f"Completed {result.completed_assessments} assessments ({result.failed_assessments} failed)")


def _build_full_export(matrix_data: dict, config: ProjectConfig) -> dict:
    """Build a full export with all matrix details."""
    export = {
        'questions': [
            {
                'key': q.key,
                'text': q.text,
                'type': q.answer_type.value,
                'options': q.options
            }
            for q in config.questions
        ],
        'sources': []
    }

    for source in matrix_data['sources']:
        source_export = {
            'id': source['id'],
            'title': source['title'],
            'authors': source['authors'],
            'year': source['year'],
            'answers': {}
        }

        source_matrix = matrix_data['matrix'].get(source['id'], {})
        for q in config.questions:
            cell = source_matrix.get(q.key, {})
            if cell:
                source_export['answers'][q.key] = {
                    'value': cell.get('answer'),
                    'confidence': cell.get('confidence'),
                    'citations': cell.get('citations', [])
                }

        export['sources'].append(source_export)

    return export


def display_keywords_tab(project_id: int = None):
    """Display keyword analysis tab."""
    st.title("Keyword Analysis")

    if project_id:
        project = get_project(project_id)
        if project:
            st.caption(f"Keywords for project: **{project['name']}**")
    else:
        st.caption("Keywords across all sources (global)")

    keyword_df = load_keyword_data(project_id)

    if keyword_df.empty:
        st.warning("No keywords found. Keywords are extracted during source import.")
        return

    # Top keywords
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Keywords")
        top_n = st.slider("Number of keywords", 10, 50, 20)
        top_keywords = keyword_df.head(top_n)

        fig = px.bar(
            top_keywords,
            x='source_count',
            y='keyword',
            orientation='h',
            title=f"Top {top_n} Keywords"
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Keyword Statistics")
        st.metric("Total Keywords", len(keyword_df))
        st.metric("Keywords with 5+ sources", len(keyword_df[keyword_df['source_count'] >= 5]))

        # Keyword search
        search = st.text_input("Search keywords")
        if search:
            matches = keyword_df[keyword_df['keyword'].str.contains(search, case=False, na=False)]
            st.dataframe(matches, use_container_width=True, hide_index=True)

    # Full keyword table
    st.subheader("All Keywords")
    st.dataframe(keyword_df, use_container_width=True, hide_index=True)


def main():
    """Main application entry point."""
    load_dotenv(find_dotenv())

    st.set_page_config(
        page_title="Literature Management",
        initial_sidebar_state="expanded",
        layout="wide"
    )

    # Initialize database
    setup_database()

    # Sidebar
    with st.sidebar:
        st.header("Literature Management")

        # Project selector
        project_id = display_project_selector()

        st.divider()

        st.subheader("Data Import")
        if st.button("Import Citations", help="Import citations from search_results/"):
            with st.spinner("Importing citations..."):
                import_citations(project_id)
                st.success("Citations imported!")
                st.rerun()

        st.divider()

        # Database stats
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sources")
            source_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM projects")
            project_count = cursor.fetchone()[0]
            st.metric("Total Sources", source_count)
            st.metric("Projects", project_count)
        except Exception:
            st.info("Database not yet initialized")

    # Tabs
    projects_tab, sources_tab, matrix_tab, keywords_tab, add_source_tab = st.tabs([
        "Projects", "Sources", "Content Matrix", "Keywords", "Add Source"
    ])

    with projects_tab:
        display_projects_tab()

    with sources_tab:
        display_sources_tab(project_id)

    with matrix_tab:
        display_content_matrix_tab(project_id)

    with keywords_tab:
        display_keywords_tab(project_id)

    with add_source_tab:
        display_add_source_tab(project_id)


if __name__ == "__main__":
    main()
