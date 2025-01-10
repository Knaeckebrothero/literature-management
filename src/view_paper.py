"""
Streamlit page for viewing individual paper assessments from the SLR database.
"""
import streamlit as st
import pandas as pd
import sqlite3
import base64
from pathlib import Path


def get_connection():
    """Create a connection to the SQLite database."""
    return sqlite3.connect('literature.db', check_same_thread=False)


def load_paper_details():
    """Load all paper details with their assessments."""
    conn = get_connection()
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
        a.is_neurosymbolic,
        a.is_development,
        a.paper_type,
        a.summary,
        a.takeaways,
        a.assessment_date,
        CASE
            WHEN a.paper_id IS NULL THEN 'Unassessed'
            WHEN a.is_neurosymbolic = 1 THEN 'Neurosymbolic'
            ELSE 'Other'
        END as assessment_status
    FROM papers p
    LEFT JOIN paper_assessments a ON p.id = a.paper_id
    ORDER BY a.assessment_date DESC, p.publication_year DESC
    """
    return pd.read_sql_query(query, conn)


def apply_filters(df, filters):
    """Apply filters to a dataframe"""
    filtered_df = df.copy()

    # Handle year filter
    if filters.get('years'):
        filtered_df = filtered_df[filtered_df['publication_year'].isin(filters['years'])]

    # Handle paper type filter
    if filters.get('paper_type') and filters['paper_type'] != "All":
        filtered_df = filtered_df[
            (filtered_df['paper_type'] == filters['paper_type']) &
            (filtered_df['paper_type'].notna())
            ]

    # Handle focus filter
    if filters.get('focus') and filters['focus'] != "All":
        if filters['focus'] == "Neurosymbolic":
            filtered_df = filtered_df[filtered_df['assessment_status'] == 'Neurosymbolic']
        else:  # "Unassessed/Other"
            filtered_df = filtered_df[filtered_df['assessment_status'].isin(['Unassessed', 'Other'])]

    # Handle development filter
    if filters.get('development') and filters['development'] != "All":
        if filters['development'] == "Yes":
            filtered_df = filtered_df[filtered_df['is_development'] == True]
        else:
            filtered_df = filtered_df[
                (filtered_df['is_development'] == False) |
                (filtered_df['is_development'].isna())
                ]

    return filtered_df


def display_paper_details(paper, papers_dir: str = "papers"):
    """Display detailed information about a single paper."""
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

    # Assessment metrics
    st.header("Assessment")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Neurosymbolic Focus",
            "Yes" if paper['is_neurosymbolic'] else "No",
            help="Whether the paper primarily focuses on neurosymbolic AI"
        )
    with col2:
        st.metric(
            "Key Development",
            "Yes" if paper['is_development'] else "No",
            help="Whether the paper presents a significant development in the field"
        )
    with col3:
        st.metric(
            "Paper Type",
            paper['paper_type'],
            help="The primary type/category of the paper"
        )

    # Detailed assessment
    if pd.notna(paper['summary']):
        st.subheader("Summary")
        st.markdown(paper['summary'])

    if pd.notna(paper['takeaways']):
        st.subheader("Key Takeaways")
        st.markdown(paper['takeaways'])

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
            st.markdown("### PDF Preview")
            st.markdown(f'<iframe src="data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}" width="100%" height="800px"></iframe>', unsafe_allow_html=True)


def papers_view(filters=None):
    """Main function for the papers view page."""
    st.title("Paper Assessments")

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
