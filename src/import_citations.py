"""
A module for processing and managing bibliographic citations and metadata.

This module encapsulates functionalities for processing bibliographic data
from various sources (e.g., BibTeX files, IEEE CSV files, Springer CSV files)
and storing them in an SQLite database. It includes handling metadata such as
DOIs, authors, titles, keywords, and other publication details. The module is
geared towards ensuring efficient deduplication and standardized data storage.
"""
import bibtexparser
import sqlite3
import pandas as pd
import hashlib
from pathlib import Path
from typing import Dict, Optional


def _standardize_doi(doi: str) -> str:
    """
    Standardizes a Digital Object Identifier (DOI) string by removing
    common URL prefixes and unnecessary whitespace.

    Parameters:
    doi: str
        The DOI string to standardize. May contain URL prefixes or
        extra whitespace.

    Returns:
    str
        The standardized DOI string with prefixes and whitespace removed.
        Returns an empty string if the input DOI is empty.
    """
    if not doi:
        return ''

    # Remove common prefixes and whitespace
    doi = doi.strip()
    prefixes = [
        'https://doi.org/',
        'http://doi.org/',
        'doi.org/'
    ]

    for prefix in prefixes:
        if doi.lower().startswith(prefix.lower()):
            doi = doi[len(prefix):]
            break

    return doi.strip()


def _generate_content_hash(title: str, authors: str, year: Optional[int]) -> str:
    """
    Generate a hash from title, authors, and year for sources without DOI.
    """
    content = f"{title.lower().strip()}|{authors.lower().strip()}|{year or ''}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _print_stats(stats: Dict[str, int]):
    # Print statistics for file processing
    print(f"New entries inserted: {stats['inserted']}")
    print(f"Duplicates skipped: {stats['duplicate']}")
    print(f"Entries without identifier: {stats['no_id']}")


class CitationProcessor:
    """
    Handles operations related to processing citations from various data sources.

    This class provides functionality for managing and processing citation data from different
    file formats (e.g., BibTeX, IEEE CSV, Springer CSV). It connects to a SQLite database
    and facilitates the insertion of sources, their metadata, and their relationships with keywords.

    Attributes:
        db_name: The name of the database file to connect to and store citation data.
        conn: The SQLite database connection object.
        project_id: Optional project ID to link imported sources to a project.
        processed_identifiers: A set to track identifiers for duplicate checks during source insertion.

    Raises:
        sqlite3.Error: For any database-related errors during processing.
    """
    def __init__(self, db_name: str = 'literature.db', project_id: Optional[int] = None):
        """
        Initialize the citation processor with database connection.

        Parameters:
            db_name: Database file name
            project_id: Optional project ID to link sources to
        """
        self.db_name = db_name
        self.project_id = project_id
        self.processed_identifiers = set()
        self.conn = sqlite3.connect(db_name)

    def __del__(self):
        if self.conn:
            self.conn.close()

    def close(self):
        if self.conn:
            self.conn.close()

    def process_keywords(self, source_id: int, keywords: list[str]):
        """
        Processes and associates keywords with a specific source in the database.

        This method is responsible for cleaning the provided list of keywords, ensuring that
        each keyword is uniquely stored in the database, and then creating a relationship
        between the specified source and its associated keywords.

        Parameters:
            source_id (int): The identifier of the source to associate with the provided keywords.
            keywords (list[str]): A list of keywords to be processed and linked to the source.

        Raises:
            sqlite3.Error: Raised if a database error occurs during any of the operations.
        """
        cursor = self.conn.cursor()

        # Clean and filter keywords
        cleaned_keywords = [kw.strip() for kw in keywords if kw.strip()]

        for keyword in cleaned_keywords:
            try:
                # Try to insert the keyword if it doesn't exist
                cursor.execute('''
                    INSERT OR IGNORE INTO keywords (keyword)
                    VALUES (?)
                ''', (keyword,))

                # Get the keyword_id (whether it was just inserted or already existed)
                cursor.execute('''
                    SELECT id FROM keywords WHERE keyword = ?
                ''', (keyword,))
                keyword_id = cursor.fetchone()[0]

                # Create the relationship between source and keyword
                cursor.execute('''
                    INSERT OR IGNORE INTO rel_keywords_sources (source_id, keyword_id)
                    VALUES (?, ?)
                ''', (source_id, keyword_id))

            except sqlite3.Error as e:
                print(f"Error processing keyword '{keyword}' for source {source_id}: {e}")

        self.conn.commit()

    def _link_to_project(self, source_id: int):
        """Link a source to the current project if project_id is set."""
        if self.project_id is None:
            return

        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO project_sources (project_id, source_id)
                VALUES (?, ?)
            ''', (self.project_id, source_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error linking source {source_id} to project {self.project_id}: {e}")

    def _insert_source(self, source_data: Dict) -> str:
        """
        Inserts a new source into the database if it is not already present.

        The method ensures that duplicate sources with the same identifier are not inserted
        by checking both a processed identifier set and the database. Sources are identified
        by DOI when available, otherwise by a content hash.

        Parameters:
            source_data (Dict): A dictionary containing details of the source such as
                'doi', 'title', 'year', 'authors', 'publication', 'source_type',
                'import_source', and optionally 'abstract', 'metadata'.

        Returns:
            str: A status indicating the result of the operation. Possible values are:
                - 'duplicate': The source already exists in the database or processed set.
                - 'inserted': The source was successfully added to the database.
                - 'no_id': The source has no DOI and insufficient data for hash.
        """
        cursor = self.conn.cursor()

        # Standardize DOI format
        doi = _standardize_doi(source_data.get('doi', ''))
        title = source_data.get('title', '').strip()
        authors = source_data.get('authors', '').strip()
        year = source_data.get('year')

        # Determine identifier
        if doi:
            identifier = doi
            identifier_type = 'doi'
        elif title:
            identifier = _generate_content_hash(title, authors, year)
            identifier_type = 'hash'
        else:
            return 'no_id'

        # Check for duplicates
        if identifier in self.processed_identifiers:
            return 'duplicate'

        cursor.execute('SELECT id FROM sources WHERE identifier = ?', (identifier,))
        existing = cursor.fetchone()
        if existing is not None:
            # Source exists, but we might still need to link it to project
            self._link_to_project(existing[0])
            return 'duplicate'

        # Insert new source
        cursor.execute('''
        INSERT INTO sources
        (identifier, identifier_type, title, authors, year, abstract, publication,
         source_type, import_source, metadata, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            identifier,
            identifier_type,
            title,
            authors,
            year,
            source_data.get('abstract', ''),
            source_data.get('publication', ''),
            source_data.get('source_type', ''),
            source_data.get('import_source', ''),
            source_data.get('metadata'),
            source_data.get('file_path')
        ))

        self.conn.commit()
        self.processed_identifiers.add(identifier)

        # Link to project if set
        source_id = cursor.lastrowid
        self._link_to_project(source_id)

        return 'inserted'

    def _get_source_id(self, identifier: str) -> Optional[int]:
        """Get the source ID for a given identifier."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM sources WHERE identifier = ?', (identifier,))
        result = cursor.fetchone()
        return result[0] if result else None

    def _process_bibtex(self, file_path: str):
        """
        Processes a BibTeX file and inserts source entries into the database.
        """
        source_file = Path(file_path).name
        stats = {'inserted': 0, 'duplicate': 0, 'no_id': 0}

        with open(file_path, 'r', encoding='utf-8') as bibtex_file:
            parser = bibtexparser.bparser.BibTexParser(common_strings=True)
            bib_database = bibtexparser.load(bibtex_file, parser)

        for entry in bib_database.entries:
            doi = entry.get('doi', '').strip()
            title = entry.get('title', '').replace('{', '').replace('}', '').strip()
            authors = entry.get('author', '')
            year = int(entry.get('year', 0)) if entry.get('year') else None

            source_data = {
                'doi': doi,
                'title': title,
                'year': year,
                'authors': authors,
                'abstract': entry.get('abstract', ''),
                'publication': entry.get('journal', entry.get('booktitle', '')),
                'source_type': 'conference' if entry.get('booktitle') else 'journal',
                'import_source': source_file.replace('_1.bib', '').replace('_2.bib', '').strip()
            }

            # Insert the source and get its result
            result = self._insert_source(source_data)
            stats[result] += 1

            # If source was inserted successfully, process its keywords
            if result == 'inserted' and entry.get('keywords'):
                identifier = _standardize_doi(doi) if doi else _generate_content_hash(title, authors, year)
                source_id = self._get_source_id(identifier)
                if source_id:
                    self.process_keywords(source_id, entry.get('keywords').split(','))

        _print_stats(stats)

    def _process_ieee_csv(self, file_path: str):
        """
        Processes a CSV file containing IEEE publication data and updates the database.
        """
        stats = {'inserted': 0, 'duplicate': 0, 'no_id': 0}
        df = pd.read_csv(file_path)

        for _, row in df.iterrows():
            doi = str(row['DOI']).strip() if pd.notna(row['DOI']) else ''
            title = str(row['Document Title']).strip() if pd.notna(row['Document Title']) else ''
            authors = str(row['Authors']).strip() if pd.notna(row['Authors']) else ''
            year = int(row['Publication Year']) if pd.notna(row['Publication Year']) else None

            source_data = {
                'doi': doi,
                'title': title,
                'year': year,
                'authors': authors,
                'abstract': str(row['Abstract']).strip() if pd.notna(row.get('Abstract')) else '',
                'publication': str(row['Publication Title']).strip() if pd.notna(row['Publication Title']) else '',
                'source_type': str(row['Document Identifier'].replace('IEEE', '').strip().lower())
                    if pd.notna(row.get('Document Identifier')) else '',
                'import_source': 'ieee'
            }

            # Insert the source and get its result
            result = self._insert_source(source_data)
            stats[result] += 1

            # If source was inserted successfully, process its keywords
            if result == 'inserted':
                identifier = _standardize_doi(doi) if doi else _generate_content_hash(title, authors, year)
                source_id = self._get_source_id(identifier)

                if source_id:
                    # Combine and process keywords
                    combined_keywords = []
                    if pd.notna(row.get('Author Keywords')):
                        combined_keywords.extend(row['Author Keywords'].split(';'))
                    if pd.notna(row.get('IEEE Terms')):
                        combined_keywords.extend(row['IEEE Terms'].split(';'))

                    self.process_keywords(source_id, combined_keywords)

        _print_stats(stats)

    def _process_springer_csv(self, file_path: str):
        """
        Processes the given Springer CSV file and extracts relevant publication data.
        """
        stats = {'inserted': 0, 'duplicate': 0, 'no_id': 0}
        df = pd.read_csv(file_path)

        for _, row in df.iterrows():
            doi = str(row['Item DOI']).strip() if pd.notna(row['Item DOI']) else ''
            title = str(row['Item Title']).strip() if pd.notna(row['Item Title']) else ''
            authors = str(row['Authors']).strip() if pd.notna(row['Authors']) else ''
            year = int(row['Publication Year']) if pd.notna(row['Publication Year']) else None

            source_data = {
                'doi': doi,
                'title': title,
                'year': year,
                'authors': authors,
                'publication': str(row['Publication Title']).strip() if pd.notna(row['Publication Title']) else '',
                'source_type': str(row['Content Type']).strip() if pd.notna(row['Content Type']) else '',
                'import_source': 'springer'
            }

            # Insert the source and get its result
            result = self._insert_source(source_data)
            stats[result] += 1

        _print_stats(stats)

    def process_files(self, file_config: Dict[str, list]):
        """
        Processes a collection of files grouped by their type.

        This method iterates through a given configuration of files grouped by file type.
        For each file, it checks if the file exists and processes it based on its type.

        Parameters:
            file_config (Dict[str, list]): A dictionary mapping file types to lists of
                file paths to be processed.

        Raises:
            Exception: Generic exception raised during the processing of each file.
        """
        try:
            for file_type, files in file_config.items():
                for file_path in files:
                    if not Path(file_path).exists():
                        print(f"File not found: {file_path}")
                        continue

                    # Process
                    print(f"\nProcessing {file_path} ({file_type}):")
                    try:
                        if file_type == 'bibtex':
                            self._process_bibtex(file_path)
                        elif file_type == 'ieee':
                            self._process_ieee_csv(file_path)
                        elif file_type == 'springer':
                            self._process_springer_csv(file_path)
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
        finally:
            self.close()
