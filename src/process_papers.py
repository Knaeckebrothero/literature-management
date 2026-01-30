"""
Module containing utility functions for working with PDFs and handling DOIs.
This includes extracting metadata such as titles, authors, and DOIs from PDFs,
and standardizing DOI formats.
"""
import re
import PyPDF2
from typing import Optional, Dict, Any
from pathlib import Path
import logging
from datetime import datetime


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
