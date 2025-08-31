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
from pathlib import Path
from typing import Dict


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


def _print_stats(stats: Dict[str, int]):
    # Print statistics for file processing
    print(f"New entries inserted: {stats['inserted']}")
    print(f"Duplicates skipped: {stats['duplicate']}")
    print(f"Entries without DOI: {stats['no_doi']}")


class CitationProcessor:
    """
    Handles operations related to processing citations from various data sources.

    This class provides functionality for managing and processing citation data from different
    file formats (e.g., BibTeX, IEEE CSV, Springer CSV). It connects to a SQLite database
    and facilitates the insertion of papers, their metadata, and their relationships with keywords.

    Attributes:
        db_name: The name of the database file to connect to and store citation data.
        conn: The SQLite database connection object.
        processed_dois: A set to track DOIs for duplicate checks during paper insertion.
        processed_titles_authors: A set to track titles and authors to identify duplicates
            in the no_doi table.

    Raises:
        sqlite3.Error: For any database-related errors during processing.
    """
    def __init__(self, db_name: str = 'literature.db'):
        """
        Initialize the citation processor with database connection
        """
        self.db_name = db_name
        self.processed_dois = set()
        self.processed_titles_authors = set()  # For checking duplicates in no_doi table
        self.conn = sqlite3.connect(db_name)


    def __del__(self):
        if self.conn:
            self.conn.close()


    def close(self):
        if self.conn:
            self.conn.close()


    def process_keywords(self, paper_id: int, keywords: list[str]):
        """
        Processes and associates keywords with a specific paper in the database.

        This method is responsible for cleaning the provided list of keywords, ensuring that
        each keyword is uniquely stored in the database, and then creating a relationship
        between the specified paper and its associated keywords. Any errors encountered during
        the database transactions are logged to provide visibility into potential issues.

        Parameters:
            paper_id (int): The identifier of the paper to associate with the provided keywords.
            keywords (list[str]): A list of keywords to be processed and linked to the paper.

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

                # Create the relationship between paper and keyword
                cursor.execute('''
                    INSERT OR IGNORE INTO rel_keywords_papers (paper_id, keyword_id)
                    VALUES (?, ?)
                ''', (paper_id, keyword_id))

            except sqlite3.Error as e:
                print(f"Error processing keyword '{keyword}' for paper {paper_id}: {e}")

        self.conn.commit()


    def _insert_paper(self, paper_data: Dict) -> str:
        """
        Inserts a new paper into the database if it is not already present.

        The method ensures that duplicate papers with the same DOI are not inserted by
        checking both a processed DOI set and the database. Additionally, it standardizes
        the DOI format before insertion to prevent mismatches due to formatting
        discrepancies.

        Parameters:
            paper_data (Dict): A dictionary containing details of the paper such as
                'doi', 'title', 'publication_year', 'authors', 'venue', 'volume',
                'publication_type', and 'publication_source'.

        Returns:
            str: A status indicating the result of the operation. Possible values are:
                - 'duplicate': The paper already exists in the database or processed DOI set.
                - 'inserted': The paper was successfully added to the database.
        """
        cursor = self.conn.cursor()

        # Standardize DOI format
        doi = _standardize_doi(paper_data.get('doi', ''))
        title = paper_data.get('title', '').strip()
        authors = paper_data.get('authors', '').strip()

        # Handle papers with DOI
        if doi in self.processed_dois:
            return 'duplicate'

        cursor.execute('SELECT doi FROM papers WHERE doi = ?', (doi,))
        if cursor.fetchone() is not None:
            return 'duplicate'

        cursor.execute('''
        INSERT INTO papers 
        (doi, title, publication_year, authors, venue, volume, publication_type, 
         publication_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (doi, title, paper_data['publication_year'], authors, paper_data['venue'],
              paper_data['volume'], paper_data['publication_type'], paper_data['publication_source']))

        self.conn.commit()
        self.processed_dois.add(doi)
        return 'inserted'


    def _process_bibtex(self, file_path: str):
        """
        Processes a BibTeX file and inserts paper entries into the database. Extracts relevant
        information from each entry in the BibTeX data, standardizes the data, and attempts to
        insert it. Keeps statistics on the number of entries processed, inserted, duplicate entries,
        and entries without DOI. Also processes keywords for successfully inserted papers.

        Parameters:
            file_path: str
                The file path to the BibTeX file to be processed.

        Raises:
            FileNotFoundError: If the specified `file_path` does not exist.
            IOError: For I/O-related issues like permission errors when accessing the file.
        """
        source_file = Path(file_path).name
        stats = {'inserted': 0, 'duplicate': 0, 'no_doi': 0}

        with open(file_path, 'r', encoding='utf-8') as bibtex_file:
            parser = bibtexparser.bparser.BibTexParser(common_strings=True)
            bib_database = bibtexparser.load(bibtex_file, parser)

        for entry in bib_database.entries:
            paper_data = {
                'doi': entry.get('doi', '').strip(),
                'title': entry.get('title', '').replace('{', '').replace('}', '').strip(),
                'publication_year': int(entry.get('year', 0)),
                'authors': entry.get('author', ''),
                'venue': entry.get('journal', entry.get('booktitle', '')),
                'volume': entry.get('volume', ''),
                # 'issue': entry.get('number', ''),
                'publication_type': 'journal' if not entry.get('journal') else 'Conference',
                'publication_source': source_file
                .replace('_1.bib', '').replace('_2.bib', '').strip()
            }

            # Insert the paper and get its result
            result = self._insert_paper(paper_data)
            stats[result] += 1

            # If paper was inserted successfully, process its keywords
            if result == 'inserted' and entry.get('keywords'):
                # Get paper_id for the newly inserted paper
                cursor = self.conn.cursor()
                cursor.execute('SELECT id FROM papers WHERE doi = ?', (_standardize_doi(paper_data['doi']),))
                paper_id = cursor.fetchone()[0]

                self.process_keywords(paper_id, entry.get('keywords').split(','))

        _print_stats(stats)


    def _process_ieee_csv(self, file_path: str):
        """
        Processes a CSV file containing IEEE publication data and updates the database accordingly.

        Summary:
        This method reads a CSV file, extracts relevant publication data, and processes the
        content to insert the information into the database. It also tracks statistics of
        inserted papers, duplicate entries, and entries without a DOI. Additionally, for newly
        inserted papers, it handles associated keywords if available.

        Parameters:
        file_path: str
            Path to the CSV file containing IEEE publication data.

        Raises:
        Any exceptions occurring during file reading, data processing, or database connections.

        Returns:
        None
        """
        stats = {'inserted': 0, 'duplicate': 0, 'no_doi': 0}
        df = pd.read_csv(file_path)

        for _, row in df.iterrows():
            paper_data = {
                'doi': str(row['DOI']).strip() if pd.notna(row['DOI']) else '',
                'title': str(row['Document Title']).strip() if pd.notna(row['Document Title']) else '',
                'publication_year': int(row['Publication Year']) if pd.notna(row['Publication Year']) else None,
                'authors': str(row['Authors']).strip() if pd.notna(row['Authors']) else '',
                'venue': str(row['Publication Title']).strip() if pd.notna(row['Publication Title']) else '',
                'volume': str(row['Volume']).strip() if pd.notna(row['Volume']) else '',
                'publication_type': str(row['Document Identifier'].replace('IEEE', '').strip().lower())
                if pd.notna(row['Document Identifier']) else '',
                'publication_source': 'ieee'
            }

            # Insert the paper and get its result
            result = self._insert_paper(paper_data)
            stats[result] += 1

            # If paper was inserted successfully, process its keywords
            if result == 'inserted':
                # Get paper_id for the newly inserted paper
                cursor = self.conn.cursor()
                cursor.execute('SELECT id FROM papers WHERE doi = ?', (_standardize_doi(paper_data['doi']),))
                paper_id = cursor.fetchone()[0]

                # Combine and process keywords
                combined_keywords = []
                if pd.notna(row.get('Author Keywords')):
                    combined_keywords.extend(row['Author Keywords'].split(';'))
                if pd.notna(row.get('IEEE Terms')):
                    combined_keywords.extend(row['IEEE Terms'].split(';'))

                self.process_keywords(paper_id, combined_keywords)

        _print_stats(stats)


    def _process_springer_csv(self, file_path: str):
        """
        Processes the given Springer CSV file and extracts relevant publication data to insert into the database.

        This method reads a Springer CSV file, extracts information such as DOI, title, publication year, authors,
        venue, volume, and publication type for each entry, and attempts to insert these details into a database
        or data store. Summary statistics of the processing (inserted, duplicate, no DOI) are printed at the end
        of the execution.

        Parameters:
            file_path: str
                The file path to the Springer CSV file.

        Raises:
            FileNotFoundError: If the provided file path does not exist.
            ValueError: If the file fails to follow the expected format or contains invalid data.
        """
        source_file = Path(file_path).name
        stats = {'inserted': 0, 'duplicate': 0, 'no_doi': 0}

        df = pd.read_csv(file_path)

        for _, row in df.iterrows():
            paper_data = {
                'doi': str(row['Item DOI']).strip() if pd.notna(row['Item DOI']) else '',
                'title': str(row['Item Title']).strip() if pd.notna(row['Item Title']) else '',
                'publication_year': int(row['Publication Year']) if pd.notna(row['Publication Year']) else None,
                'authors': str(row['Authors']).strip() if pd.notna(row['Authors']) else '',
                'venue': str(row['Publication Title']).strip() if pd.notna(row['Publication Title']) else '',
                'volume': str(row['Journal Volume']).strip() if pd.notna(row.get('Journal Volume')) else '',
                # 'issue': str(row['Journal Issue']).strip() if pd.notna(row.get('Journal Issue')) else '',
                'publication_type': str(row['Content Type']).strip() if pd.notna(row['Content Type']) else '',
                'publication_source': 'springer'
            }

            # Insert the paper and get its result
            result = self._insert_paper(paper_data)
            stats[result] += 1

        _print_stats(stats)


    def process_files(self, file_config: Dict[str, list]):
        """
        Processes a collection of files grouped by their type.

        This method iterates through a given configuration of files grouped by file type.
        For each file, it checks if the file exists and processes it based on its type. If
        the file is not found or an error occurs during processing, it logs the relevant
        information. The method handles 'bibtex', 'ieee', and 'springer' file types using
        dedicated internal processing functions. It ensures system resources are properly
        released by calling the `close` method regardless of any processing errors.

        Parameters:
            file_config (Dict[str, list]): A dictionary mapping file types to lists of
                file paths to be processed.

        Raises:
            Exception: Generic exception raised during the processing of each file to
                log specific errors encountered during file processing.
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
