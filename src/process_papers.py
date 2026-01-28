"""
Module containing utility classes and functions for working with PDFs and
handling DOIs. This includes extracting metadata such as titles, authors,
and DOIs from PDFs, and standardizing DOI formats.

The key functionality provided includes:
- A `RateLimiter` class for controlling API request rates.
- Functions to standardize DOIs and extract metadata from academic PDF files.
"""
import sqlite3
import re
import PyPDF2
import time
from typing import Optional, Dict, Any
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.llms import Replicate
from assessment.virtual_tutor_assessment import VirtualTutorAssessment
import logging
from datetime import datetime


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Implements a Rate Limiter mechanism to regulate the frequency of requests.

    This class ensures that requests are made at a controlled rate by enforcing a
    delay between consecutive requests. The delay is derived from the maximum
    allowed requests per minute configuration.

    Attributes:
        delay: Duration in seconds to wait between consecutive requests.
        last_request: Timestamp of the most recent request.
    """
    def __init__(self, requests_per_minute: int = 20):
        self.delay = 60.0 / requests_per_minute
        self.last_request = 0

    def wait(self):
        """
        Waits for a certain delay before allowing the next request.

        This method ensures that a specified time delay is maintained between
        requests. If the time since the last request is less than the required
        delay, it pauses execution for the remaining time. Otherwise, it
        immediately updates the timestamp to allow the next request.

        Raises:
            ValueError: If the delay or the calculated sleep time is invalid.
        """
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request = time.time()


def standardize_doi(doi: str) -> Optional[str]:
    """
    Standardizes a DOI (Digital Object Identifier) string into a canonical format that
    removes prefixes, adjusts case, and ensures the DOI adheres to specific patterns.

    This function identifies and standardizes DOIs that match various formats
    commonly used across different organizations or publications. The DOI is first
    cleaned by removing common prefixes and then matched against a list of predefined
    regular expression patterns. For ACM DOIs, specific standardization is applied to
    ensure consistent formatting.

    Parameters:
        doi: str
            The input DOI string to be standardized.

    Returns:
        Optional[str]: The standardized DOI string, or None if no valid DOI is found.
    """
    if not doi:
        return None

    # print(f"Original DOI string: {doi}")

    # Remove common prefixes and whitespace
    doi = doi.lower().strip()
    prefixes = [
        'https://doi.org/',
        'http://doi.org/',
        'doi.org/',
        'doi:',
        'doi: ',
        'digital object identifier ',
        'digital object identifier: '
    ]

    for prefix in prefixes:
        if doi.startswith(prefix):
            doi = doi[len(prefix):]

    # print(f"After prefix removal: {doi}")

    # Define patterns for different DOI formats
    patterns = [
        # ACM specific patterns
        r'10\.1145/\d{7}\.\d{7}\b',
        r'10\.1145/\d{6,7}\b',  # Shorter ACM DOIs
        # IEEE conference and journal patterns
        r'10\.1109/[A-Z]+\d+\.\d+\.\d+',
        r'10\.1109/[A-Z]+\.\d{4}\.\d{7}',
        # Wiley patterns
        r'10\.1002/[a-z]+\.\d{4}',
        r'10\.1002/[a-z]+\.\d{4,5}',
        # Russian journal pattern
        r'10\.3103/S\d{13}\b',
        # General DOI patterns with optional suffix
        r'10\.\d{4,5}/[-._;()\/:A-Z0-9]+',
        # Alternative format with S-prefixed numbers
        r'10\.\d{4}/S\d+',
        # Handle DOIs embedded in URLs
        r'(?<=doi\.org/)(10\.\d{4,5}/[-._;()\/:A-Z0-9]+)',
        # Alternative format sometimes used
        r'10/[-._;()\/:A-Z0-9]+\.\d{4}',
        # ACM format with year
        r'10\.1145/\d{7}(?:\.\d{0,7})?',
    ]

    # Try each pattern
    for pattern in patterns:
        matches = re.finditer(pattern, doi, re.IGNORECASE)
        dois = [match.group(0) for match in matches]
        if dois:
            raw_doi = dois[0]
            print(f"Found DOI with pattern {pattern}: {raw_doi}")

            # Standardize ACM DOIs
            if raw_doi.startswith('10.1145/'):
                try:
                    prefix, numbers = raw_doi.split('/')
                    base, suffix = numbers.split('.')
                    base = base[:7]  # Take first 7 digits
                    suffix = suffix[:7]  # Take first 7 digits
                    standardized = f"{prefix}/{base}.{suffix}"
                    print(f"Standardized ACM DOI: {standardized}")
                    return standardized
                except Exception as e:
                    print(f"Error standardizing ACM DOI: {e}")
                    continue

            return raw_doi

    return None


def extract_doi_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extracts the DOI (Digital Object Identifier) from the specified PDF file.

    This function searches for DOI information by first checking the metadata of the PDF,
    and then by scanning the first few pages of the document for potential DOI patterns
    or related phrases. If a DOI is found, it is extracted, standardized, and returned.
    The function uses typical DOI format and common phrases like "doi", "10.1002/", etc.,
    to identify potential DOI markers.

    Errors encountered during the reading or parsing process are silently handled by
    printing an error message, while the function returns None in such cases.

    Parameters:
        pdf_path (str): The path to the PDF file from which the DOI needs to be extracted.

    Returns:
        Optional[str]: The standardized DOI string if found; None otherwise.

    Raises:
        None
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)

            # Try metadata first
            if pdf.metadata and '/doi' in pdf.metadata:
                doi = standardize_doi(pdf.metadata['/doi'])
                if doi:
                    return doi

            # Search first few pages
            search_phrases = [
                'doi',
                'digital object identifier',
                'https://doi.org',
                'doi.org',
                '10.1109/',  # IEEE
                '10.1145/',  # ACM
                '10.1007/',  # Springer
                '10.3103/',  # Russian journals
                '10.1002/',  # Wiley
                'acm.org',
                'permission',
                'copyright',
                '©',
                'received:',
                'revised:',
                'accepted:'
            ]

            # Expand search range to catch DOIs that might appear later
            for i in range(min(5, len(pdf.pages))):
                text = pdf.pages[i].extract_text().lower()
                lines = text.split('\n')

                # First try to find lines containing DOI indicators
                for line in lines:
                    if any(phrase in line.lower() for phrase in search_phrases):
                        doi = standardize_doi(line)
                        if doi:
                            return doi

                # If no DOI found with indicators, try pattern matching on all lines
                # This catches cases where DOI appears without explicit marking
                for line in lines:
                    doi = standardize_doi(line)
                    if doi:
                        return doi

            return None

    except Exception as e:
        print(f"Error extracting DOI from {pdf_path}: {e}")
        return None


def extract_title_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extracts the title of a PDF document using metadata or the first page text.

    This function attempts to extract the title from the PDF document specified by
    `pdf_path`. The extraction process first checks the metadata of the PDF for a
    title. If no metadata title is found, it examines the text on the first page
    of the document, using a heuristic to identify a plausible title candidate.

    Parameters:
    pdf_path: str
        The file path of the PDF document from which to extract the title.

    Returns:
    Optional[str]
        The extracted title if identified, or None if a title could not be
        determined or an error occurred.

    Raises:
    None
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)

            # Try metadata first
            if pdf.metadata and '/Title' in pdf.metadata:
                return pdf.metadata['/Title'].strip()

            # Try first page
            first_page_text = pdf.pages[0].extract_text()
            lines = first_page_text.split('\n')

            # Usually the title is one of the first non-empty lines
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line and len(line) > 20:  # Basic heuristic for title-like text
                    return line

            return None
    except Exception as e:
        print(f"Error extracting title from {pdf_path}: {e}")
        return None


def extract_authors_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract authors from a PDF file.

    This function attempts to fetch the authors of a document provided in PDF format. It first
    tries to extract the authors from the PDF metadata. If the metadata does not contain
    author information, the function attempts to identify potential author names from the
    text present on the first page of the document. It leverages patterns such as the proximity
    of the author list to the title or keywords like 'abstract', 'introduction', and 'keywords'
    to determine probable author entries. The resulting author names, if any, are returned
    as a string. If authors cannot be identified or in case of any failure, the function
    returns None.

    Attributes:
        pdf_path (str): Path to the PDF file from which authors are to be extracted.

    Errors Raised:
        Any exceptions arising during the file reading or processing are caught and logged,
        and the function will safely return None instead.

    Returns:
        Optional[str]: A string containing names of identified authors, or None if authors
        cannot be determined.
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)

            # Try metadata first
            if pdf.metadata and '/Author' in pdf.metadata:
                return pdf.metadata['/Author'].strip()

            # Try to extract from first page
            first_page_text = pdf.pages[0].extract_text()
            lines = first_page_text.split('\n')

            # Look for author patterns (usually after title)
            title = extract_title_from_pdf(pdf_path)
            if title:
                title_lower = title[:30].lower()
                for i, line in enumerate(lines):
                    if title_lower in line.lower() and i + 1 < len(lines):
                        # Authors often appear right after title
                        potential_authors = []
                        for j in range(i + 1, min(i + 5, len(lines))):
                            next_line = lines[j].strip()
                            # Stop if we hit abstract or other sections
                            if any(kw in next_line.lower() for kw in ['abstract', 'introduction', 'keywords', '1.']):
                                break
                            if next_line and len(next_line) > 5:
                                potential_authors.append(next_line)

                        if potential_authors:
                            return ', '.join(potential_authors[:2])  # Take first 2 lines as authors

            return None
    except Exception as e:
        logger.error(f"Error extracting authors from {pdf_path}: {e}")
        return None


def extract_year_from_pdf(pdf_path: str) -> Optional[int]:
    """
    Extracts the publication year from a PDF file.

    This function attempts to determine the publication year of the given PDF file by:
    - Checking the PDF metadata for a creation date.
    - Searching for specific patterns such as arXiv identifiers, copyright years,
      or other common year patterns within the text of the first few pages.

    If multiple year candidates are found in the text, the function returns the
    most recent valid year. The valid year range is restricted to 1990 through the
    next calendar year from the current system date.

    Attributes:
        logger: Logging instance used for error reporting.

    Parameters:
        pdf_path: str
            The file path of the PDF to analyze.

    Returns:
        Optional[int]: Detected publication year, or None if no valid year is found.

    Raises:
        Any exceptions encountered during file processing or text extraction
        are logged, and the function returns None.
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)

            # Try metadata first
            if pdf.metadata and '/CreationDate' in pdf.metadata:
                date_str = pdf.metadata['/CreationDate']
                # Parse PDF date format (D:YYYYMMDDHHmmSS)
                year_match = re.search(r'D:(\d{4})', date_str)
                if year_match:
                    return int(year_match.group(1))

            # Search for year patterns in first few pages
            for i in range(min(3, len(pdf.pages))):
                text = pdf.pages[i].extract_text()

                # Look for arXiv pattern
                arxiv_match = re.search(r'arXiv:(\d{2})(\d{2})\.\d{4,5}', text)
                if arxiv_match:
                    year = int('20' + arxiv_match.group(1))
                    return year

                # Look for copyright year
                copyright_match = re.search(r'©\s*(\d{4})', text)
                if copyright_match:
                    return int(copyright_match.group(1))

                # Look for common year patterns
                year_patterns = [
                    r'(19|20)\d{2}',  # Basic year
                    r'published.*?(19|20)\d{2}',
                    r'accepted.*?(19|20)\d{2}',
                    r'submitted.*?(19|20)\d{2}'
                ]

                for pattern in year_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        # Get the most recent year
                        years = [int(m) if isinstance(m, str) and m.isdigit() else int(m[0] + m[1])
                                 for m in matches if isinstance(m, (str, tuple))]
                        valid_years = [y for y in years if 1990 <= y <= datetime.now().year + 1]
                        if valid_years:
                            return max(valid_years)

            return None
    except Exception as e:
        logger.error(f"Error extracting year from {pdf_path}: {e}")
        return None


def extract_full_metadata_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts comprehensive metadata from a specified PDF file, including attributes
    such as DOI, title, authors, year, and venue. The extraction process attempts to
    determine these attributes using a combination of auxiliary helper functions and
    direct parsing of the PDF file's content.

    Attributes like DOI, title, authors, and year are determined using specialized
    helper functions, while the venue is defaulted to 'arXiv'. The function also
    searches for an arXiv ID within the first few pages of the PDF, and attempts to
    derive the year from the arXiv ID if other methods for year extraction fail.

    Extensive fallbacks are implemented in case specific metadata elements cannot
    be extracted, ensuring that the function provides a complete metadata dictionary
    even when specific sources are unavailable or malformed.

    Parameters:
        pdf_path: str
            The path to the PDF file from which metadata is to be extracted.

    Returns:
        Dict[str, Any]
            A dictionary containing extracted metadata. It includes the following
            entries:
            - 'doi': DOI of the document, if available, otherwise None.
            - 'title': Title of the document, extracted or derived from filename.
            - 'authors': Authors of the document, extracted or defaulted to
              'Unknown Authors'.
            - 'year': Year of publication, extracted or defaulted to the current year.
            - 'venue': "arXiv".
            - 'arxiv_id': arXiv ID extracted from the document, if found, otherwise None.

    Raises:
        None
    """
    metadata = {
        'doi': extract_doi_from_pdf(pdf_path),
        'title': extract_title_from_pdf(pdf_path),
        'authors': extract_authors_from_pdf(pdf_path),
        'year': extract_year_from_pdf(pdf_path),
        'venue': 'arXiv',
        'arxiv_id': None
    }

    try:
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)

            # Search first pages for arXiv patterns
            for i in range(min(3, len(pdf.pages))):
                text = pdf.pages[i].extract_text()

                # Look for arXiv ID (e.g., arXiv:2401.12345)
                arxiv_match = re.search(r'arXiv:(\d{4}\.\d{4,5})', text)
                if arxiv_match:
                    metadata['arxiv_id'] = arxiv_match.group(1)
                    # Extract year from arXiv ID if not already found
                    if not metadata['year']:
                        year = int('20' + arxiv_match.group(1)[:2])
                        if 2000 <= year <= datetime.now().year + 1:
                            metadata['year'] = year
                    break

    except Exception as e:
        logger.error(f"Error extracting full metadata from {pdf_path}: {e}")

    # Set defaults if not found
    if not metadata['title']:
        metadata['title'] = Path(pdf_path).stem  # Use filename as fallback
    if not metadata['authors']:
        metadata['authors'] = 'Unknown Authors'
    if not metadata['year']:
        metadata['year'] = datetime.now().year

    return metadata


class PdfProcessor:
    """
    Class responsible for processing PDF files, extracting metadata, and interacting with a database
    for papers and assessments.

    The PdfProcessor class is designed to streamline the handling of PDF files in the context of
    academic papers. It manages database connections, processes PDF files to extract metadata,
    checks for the existence of papers in the database, and facilitates the assessment of papers
    using specific models. Additionally, the class includes mechanisms for rate-limiting requests
    and ensures normalized handling of list-based assessment fields.

    Attributes:
        conn: Database connection object for storing and retrieving paper information.
        llm_open_ai: Instance of a ChatOpenAI model for processing tasks.
        llm_llama: Instance of a Replicate-based model for advanced processing.
        assessment: Instance of VirtualTutorAssessment for assessing the content of PDFs.
        rate_limiter: A rate limiter to control the number of requests sent per minute.

    Methods:
        __del__:
            Closes the database connection when the object is deleted.
        close:
            Closes the database connection explicitly.
        create_paper_from_pdf:
            Extracts metadata from the PDF and creates a new paper database entry.
        find_paper_id:
            Identifies if a paper from a given PDF exists in the database based on DOI or title.
        process_pdf:
            Processes the content of a single PDF and rates it for assessment while respecting rate limits.
        save_assessment:
            Stores the assessment results for a paper in the database while managing normalized list fields.
    """
    def __init__(self, db_path: str = 'literature.db'):
        self.conn = sqlite3.connect(db_path)

        # Initialize LangChain components
        self.llm_open_ai = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1,
            seed=3459746589468594
        )
        self.llm_llama = Replicate(
            model="meta/meta-llama-3.1-405b-instruct",
            model_kwargs={
                "top_k": 50,
                "top_p": 1,
                "temperature": 0.1,
                "max_tokens": 65536,
                "seed": 3459746589468594
            },
        )

        # Initialize the assessment class
        self.assessment = VirtualTutorAssessment(model=self.llm_open_ai)

        # Initialize rate limiter (20 requests per minute)
        self.rate_limiter = RateLimiter(requests_per_minute=20)

    def __del__(self):
        if self.conn:
            self.conn.close()

    def close(self):
        if self.conn:
            self.conn.close()

    def create_paper_from_pdf(self, pdf_path: str) -> Optional[int]:
        """
        Creates a new paper entry in the database from a given PDF file.

        This method attempts to extract metadata from a PDF file and use it to create a new
        entry in the papers database. It also prevents duplicate entries by checking
        if a paper with the same title already exists. If a sufficient metadata payload
        is not found or an error occurs during the insertion process, the method handles
        it appropriately and logs relevant information.

        Parameters:
        pdf_path: str
            The file path of the PDF from which metadata will be extracted.

        Returns:
        Optional[int]
            The ID of the newly created paper entry if successful, the ID
            of an existing paper entry if a duplicate is detected, or None
            if the operation fails.
        """
        logger.info(f"Attempting to create paper entry from PDF: {pdf_path}")

        metadata = extract_full_metadata_from_pdf(pdf_path)

        # Need at least a title to create an entry
        if not metadata.get('title'):
            logger.warning(f"Could not extract sufficient metadata from {pdf_path}")
            return None

        # Check if paper with same title already exists
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM papers WHERE LOWER(title) = LOWER(?)', (metadata['title'],))
        existing = cursor.fetchone()
        if existing:
            logger.info(f"Paper with title '{metadata['title']}' already exists with ID {existing[0]}")
            return existing[0]

        # Insert into database
        try:
            cursor.execute('''
                           INSERT INTO papers
                           (doi, title, publication_year, authors, venue, volume, publication_type,
                            publication_source, processed, file_path)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                           ''', (
                               metadata.get('doi', ''),
                               metadata['title'],
                               metadata['year'],
                               metadata['authors'],
                               metadata['venue'],
                               metadata.get('arxiv_id', ''),  # Store arxiv ID in volume field
                               'preprint',
                               'arxiv_auto_import',
                               0,
                               pdf_path
                           ))

            self.conn.commit()
            paper_id = cursor.lastrowid
            logger.info(f"Created new paper entry with ID {paper_id} for '{metadata['title']}'")
            return paper_id

        except Exception as e:
            logger.error(f"Error creating paper entry: {e}")
            return None

    def find_paper_id(self, pdf_path: str) -> Optional[int]:
        """
        Attempts to find the ID of a paper in the database by analyzing the given PDF.

        It first tries to extract and match the DOI (Document Object Identifier) from the PDF against the database.
        If no match is found via DOI, it attempts to extract the title from the PDF and matches it to the titles in the database.
        The matching process for the title involves cleaning the title string and employing a pattern-matching technique for flexibility.

        Parameters:
            pdf_path: str
                The file path of the PDF from which the paper ID needs to be determined.

        Returns:
            Optional[int]
                The ID of the paper if found in the database, otherwise None.

        Raises:
            Any database-related errors or exceptions raised by internal operations are not handled directly in this function.
        """
        cursor = self.conn.cursor()

        # Try DOI first
        doi = extract_doi_from_pdf(pdf_path)
        if doi:
            # Debug: Print all DOIs in database for comparison
            cursor.execute('SELECT doi FROM papers')
            all_dois = [row[0] for row in cursor.fetchall()]
            print(f"Found DOI in PDF: {doi}")
            print(f"Looking for match among database DOIs: {all_dois[:5]}...")  # Show first 5 for brevity

            # Try exact match first
            cursor.execute('SELECT id FROM papers WHERE doi = ?', (doi,))
            result = cursor.fetchone()
            if result:
                return result[0]

            # If no exact match, try case-insensitive match
            cursor.execute('SELECT id FROM papers WHERE LOWER(doi) = LOWER(?)', (doi,))
            result = cursor.fetchone()
            if result:
                return result[0]

            # If still no match, try without any potential trailing characters
            base_doi = re.match(r'(10\.\d{4,5}/[^/\s]+)', doi)
            if base_doi:
                cursor.execute('SELECT id FROM papers WHERE doi LIKE ?', (f"{base_doi.group(1)}%",))
                result = cursor.fetchone()
                if result:
                    return result[0]

            print(f"DOI {doi} not found in database with any matching method, trying title matching...")

        # Fallback to title matching
        title = extract_title_from_pdf(pdf_path)
        if title:
            print(f"Attempting to match title: {title}")

            # Clean the title for better matching
            clean_title = re.sub(r'[^\w\s-]', '', title.lower())
            words = clean_title.split()
            if len(words) > 3:  # Only try if we have enough words to make a meaningful match
                # Create a LIKE pattern matching any 3 consecutive words
                patterns = []
                for i in range(len(words) - 2):
                    pattern = f"%{words[i]}%{words[i+1]}%{words[i+2]}%"
                    patterns.append(pattern)

                # Try each pattern
                for pattern in patterns:
                    cursor.execute('''
                                   SELECT id, title
                                   FROM papers
                                   WHERE LOWER(REPLACE(title, ':', '')) LIKE ?
                                   ''', (pattern,))

                    results = cursor.fetchall()
                    if results:
                        print(f"Found {len(results)} potential matches:")
                        for r in results:
                            print(f"ID: {r[0]}, Title: {r[1]}")
                        return results[0][0]  # Return first match

            print(f"No title matches found using any pattern")

        print(f"No matching paper found for {pdf_path}")
        return None

    def process_pdf(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        Processes a PDF file, extracts its content, and assesses it for relevancy to virtual tutors. If the
        paper does not match the assessment criteria, it is considered irrelevant and ignored.

        Args:
            pdf_path (str): The path to the PDF file to be processed.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the assessment results if the paper
            is relevant, or None if the paper is irrelevant or an error occurs during processing.
        """
        try:
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()

            # Combine pages into a single text
            content = ""
            for page in pages:
                content += page.page_content + "\n"

            # Rate limit and assess
            self.rate_limiter.wait()
            assessment = self.assessment.assess_paper(content)

            if assessment is None:
                logger.info(f"Paper {pdf_path} is not about virtual tutors")
                return None

            return assessment

        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            return None

    def save_assessment(self, paper_id: int, assessment: Dict[str, Any]):
        """
        Saves assessment data into the database by inserting scalar fields into the main assessment table
        and list fields into their respective sub-tables. Handles transactions to ensure data consistency
        and utilizes parameterized SQL queries for security and flexibility.

        Attributes
        ----------
        conn : sqlite3.Connection
            Database connection object used to execute SQL queries.

        Parameters
        ----------
        paper_id : int
            The unique identifier of the paper associated with this assessment.
        assessment : Dict[str, Any]
            A dictionary containing assessment data, where keys correspond to database fields and
            values are either scalar types or lists. List fields are stored in specific sub-tables,
            while scalar fields are stored in the main assessment table.

        Raises
        ------
        Exception
            If an error occurs during the database operations, the transaction is rolled back and
            the error is logged before being raised.

        Notes
        -----
        - List fields are stored in separate sub-tables. Any existing entries for the specified paper ID
          in these sub-tables are deleted before inserting new data.
        - Handles both scalar values and lists for the list fields. Individual strings with commas are
          split into lists.
        - The `assessment_date` field is automatically added with the current ISO 8601 datetime.
        - Type consistency is enforced for list fields, ensuring values are appropriately handled.
        - All operations are wrapped in a single transaction for atomicity.
        """
        cursor = self.conn.cursor()

        # Define which fields are lists and their corresponding tables
        list_field_mappings = {
            'architecture_components': 'assessment_architecture_components',
            'interaction_modality': 'assessment_interaction_modalities',
            'analytics_features': 'assessment_analytics_features',
            'pedagogical_features': 'assessment_pedagogical_features',
            'collaboration_types': 'assessment_collaboration_types',
            'aspects_evaluated': 'assessment_aspects_evaluated'
        }

        try:
            # Start a transaction
            cursor.execute("BEGIN TRANSACTION")

            # Separate list fields from scalar fields
            scalar_fields = {}
            list_fields = {}

            for field, value in assessment.items():
                if field in list_field_mappings:
                    # This is a list field - handle it separately even if value is None
                    if value:
                        # Handle list fields with values
                        if isinstance(value, str) and ',' in value:
                            # Already comma-separated (from _flatten_assessment)
                            list_fields[field] = [v.strip() for v in value.split(',')]
                        elif isinstance(value, list):
                            list_fields[field] = value
                        else:
                            # Single value, treat as list
                            list_fields[field] = [value]
                    # If value is None or empty, we simply don't add it to list_fields
                    # and don't add it to scalar_fields either
                else:
                    # Only non-list fields go to scalar_fields
                    scalar_fields[field] = value

            # Insert scalar fields into main assessment table
            scalar_fields['assessment_date'] = datetime.now().isoformat()
            scalar_fields['paper_id'] = paper_id

            # Build SQL for scalar fields only
            field_names = ','.join(scalar_fields.keys())
            placeholders = ','.join(['?' for _ in scalar_fields])
            values = list(scalar_fields.values())

            cursor.execute(f'''
                INSERT OR REPLACE INTO virtual_tutor_assessments
                ({field_names})
                VALUES ({placeholders})
            ''', values)

            # Insert list fields into their respective tables
            for field, items in list_fields.items():
                table_name = list_field_mappings[field]

                # First, delete existing entries for this paper
                cursor.execute(f"DELETE FROM {table_name} WHERE paper_id = ?", (paper_id,))

                # Then insert new entries
                if items and items != ['']:  # Skip empty lists
                    # Determine column name based on table
                    if 'collaboration_type' in table_name:
                        col_name = 'collaboration_type'
                    elif 'component' in table_name:
                        col_name = 'component'
                    elif 'modalit' in table_name:  # matches both modality and modalities
                        col_name = 'modality'
                    elif 'feature' in table_name:
                        col_name = 'feature'
                    elif 'aspect' in table_name:
                        col_name = 'aspect'
                    else:
                        col_name = 'value'  # fallback

                    for item in items:
                        if item and item.strip():  # Skip empty strings
                            cursor.execute(
                                f"INSERT INTO {table_name} (paper_id, {col_name}) VALUES (?, ?)",
                                (paper_id, item.strip())
                            )

            # Commit the transaction
            cursor.execute("COMMIT")
            logger.info(f"Assessment saved for paper {paper_id}")

        except Exception as e:
            # Rollback on error
            cursor.execute("ROLLBACK")
            logger.error(f"Error saving assessment: {e}")
            raise

    def process_directory(self, directory_path: str, create_missing: bool = False):
        """
        Processes all PDF files in the given directory, attempts to find or create paper entries,
        and processes each paper to extract an assessment. Provides comprehensive logging information
        about successes, failures, and skipped files due to specific conditions.

        Parameters:
        directory_path: str
            The path to the directory containing PDF files for processing.
        create_missing: bool, optional
            If set to True, attempts to create a new database entry for a paper using PDF metadata
            if no matching paper exists (default is False).

        Raises:
        Exception
            If an error occurs while processing a PDF, logs the error and skips the file.
        """
        pdf_files = Path(directory_path).glob('*.pdf')

        for pdf_path in pdf_files:
            logger.info(f"\nProcessing {pdf_path.name}...")

            try:
                # Find paper ID
                paper_id = self.find_paper_id(str(pdf_path))

                if not paper_id and create_missing:
                    # Try to create entry from PDF metadata
                    logger.info(f"Paper not found in database, attempting to create entry from PDF metadata...")
                    paper_id = self.create_paper_from_pdf(str(pdf_path))

                if not paper_id:
                    logger.warning(f"No matching paper found for {pdf_path.name}, skipping...")
                    continue

                logger.info(f"Paper ID -> {paper_id}")

                # Check page count
                with open(pdf_path, 'rb') as file:
                    pdf = PyPDF2.PdfReader(file)
                    if len(pdf.pages) > 40:
                        logger.warning(f"Skipping {pdf_path} due to excessive page count")
                        self._mark_paper_unprocessed(paper_id)
                        continue

                # Process PDF
                assessment = self.process_pdf(str(pdf_path))
                if assessment:
                    self.save_assessment(paper_id, assessment)
                    self._mark_paper_processed(paper_id, str(pdf_path))
                else:
                    logger.warning(f"Paper {pdf_path.name} is not about virtual tutors")
                    self._mark_paper_unprocessed(paper_id)

            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}")
                continue

        logger.info("All PDFs processed.")
        self.conn.commit()

    def _mark_paper_processed(self, paper_id: int, file_path: str):
        """
        Marks a paper as processed by updating its file path and setting its processed
        status to true in the database.

        Parameters:
        paper_id : int
            The unique identifier of the paper to be updated.
        file_path : str
            The file path of the processed paper.

        Raises:
        Exception
            If there is an issue with database interaction.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
                       UPDATE papers
                       SET file_path = ?, processed = 1
                       WHERE id = ?
                       ''', (file_path, paper_id))
        self.conn.commit()

    def _mark_paper_unprocessed(self, paper_id: int):
        """
        Marks a paper as unprocessed in the database.

        This method updates the 'processed' status of a specific paper in the papers
        table identified by its ID, setting the processed flag to 0.

        Args:
            paper_id (int): The ID of the paper to be marked as unprocessed.
        """
        cursor = self.conn.cursor()
        cursor.execute('''
                       UPDATE papers
                       SET processed = 0
                       WHERE id = ?
                       ''', (paper_id,))
        self.conn.commit()
