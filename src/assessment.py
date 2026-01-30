"""
Assessment Loop for SLR Content Matrix.

Orchestrates the assessment of sources against project questions,
storing results in the content_matrix table.
"""
import json
import logging
import sqlite3
from dataclasses import dataclass
from typing import Callable, Iterator, Optional

from models import Answer, AssessmentResult, ProjectConfig, Question


logger = logging.getLogger(__name__)


@dataclass
class SourceData:
    """Minimal source data for assessment."""
    id: int
    title: str
    abstract: str
    content: Optional[str] = None

    @property
    def assessment_text(self) -> str:
        """Get the text to use for assessment (prefer full content, fall back to abstract)."""
        if self.content and len(self.content) > len(self.abstract or ''):
            return self.content
        return self.abstract or ''


@dataclass
class AssessmentProgress:
    """Progress tracking for assessment."""
    total_sources: int
    total_questions: int
    completed_assessments: int
    failed_assessments: int
    current_source: Optional[str] = None
    current_question: Optional[str] = None

    @property
    def total_cells(self) -> int:
        """Total number of cells in the matrix."""
        return self.total_sources * self.total_questions

    @property
    def progress_pct(self) -> float:
        """Progress as percentage."""
        if self.total_cells == 0:
            return 100.0
        return (self.completed_assessments / self.total_cells) * 100


class AssessmentRunner:
    """
    Runs assessment for a project's content matrix.

    Iterates over sources and questions, calling the agent for each pair
    and storing results in the database.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        project_id: int,
        config: ProjectConfig,
        agent,  # AssessmentAgent
    ):
        """
        Initialize the assessment runner.

        Args:
            conn: Database connection
            project_id: ID of the project being assessed
            config: Project configuration with questions
            agent: AssessmentAgent instance
        """
        self.conn = conn
        self.project_id = project_id
        self.config = config
        self.agent = agent

    def get_sources(self) -> list[SourceData]:
        """Load sources for this project."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.id, s.title, s.abstract, s.content
            FROM sources s
            JOIN project_sources ps ON s.id = ps.source_id
            WHERE ps.project_id = ?
            ORDER BY s.id
        """, (self.project_id,))

        sources = []
        for row in cursor.fetchall():
            sources.append(SourceData(
                id=row[0],
                title=row[1] or '',
                abstract=row[2] or '',
                content=row[3]
            ))
        return sources

    def get_pending_assessments(
        self,
        sources: list[SourceData],
        questions: list[Question],
    ) -> Iterator[tuple[SourceData, Question]]:
        """
        Yield (source, question) pairs that haven't been assessed yet.

        Args:
            sources: List of sources to assess
            questions: List of questions to ask

        Yields:
            Tuples of (SourceData, Question) for pending assessments
        """
        cursor = self.conn.cursor()

        # Get existing assessments for this project
        cursor.execute("""
            SELECT source_id, question_key
            FROM content_matrix
            WHERE project_id = ?
        """, (self.project_id,))
        existing = {(row[0], row[1]) for row in cursor.fetchall()}

        for source in sources:
            for question in questions:
                if (source.id, question.key) not in existing:
                    yield (source, question)

    def store_answer(self, source_id: int, answer: Answer, question: Question):
        """Store an answer in the content_matrix table."""
        cursor = self.conn.cursor()

        # Determine answer_type from question
        answer_type = question.answer_type.value

        # Serialize citations
        citations_json = json.dumps([c.model_dump() for c in answer.citations])

        cursor.execute("""
            INSERT INTO content_matrix
            (project_id, source_id, question_key, answer, answer_type, confidence, citations)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (project_id, source_id, question_key) DO UPDATE SET
                answer = excluded.answer,
                answer_type = excluded.answer_type,
                confidence = excluded.confidence,
                citations = excluded.citations
        """, (
            self.project_id,
            source_id,
            answer.question_key,
            str(answer.value) if answer.value is not None else None,
            answer_type,
            answer.confidence.value,
            citations_json
        ))
        self.conn.commit()

    def run(
        self,
        progress_callback: Optional[Callable[[AssessmentProgress], None]] = None,
        skip_existing: bool = True,
    ) -> AssessmentProgress:
        """
        Run the assessment for all sources and questions.

        Args:
            progress_callback: Optional callback for progress updates
            skip_existing: If True, skip already-assessed (source, question) pairs

        Returns:
            Final AssessmentProgress with completion stats
        """
        sources = self.get_sources()
        questions = self.config.questions

        if not sources:
            logger.warning(f"No sources found for project {self.project_id}")
            return AssessmentProgress(
                total_sources=0,
                total_questions=len(questions),
                completed_assessments=0,
                failed_assessments=0
            )

        if not questions:
            logger.warning(f"No questions configured for project {self.project_id}")
            return AssessmentProgress(
                total_sources=len(sources),
                total_questions=0,
                completed_assessments=0,
                failed_assessments=0
            )

        progress = AssessmentProgress(
            total_sources=len(sources),
            total_questions=len(questions),
            completed_assessments=0,
            failed_assessments=0
        )

        # Get pending assessments
        if skip_existing:
            pending = list(self.get_pending_assessments(sources, questions))
        else:
            pending = [(s, q) for s in sources for q in questions]

        logger.info(
            f"Running assessment: {len(sources)} sources, {len(questions)} questions, "
            f"{len(pending)} pending assessments"
        )

        for source, question in pending:
            progress.current_source = source.title[:50]
            progress.current_question = question.key

            if progress_callback:
                progress_callback(progress)

            # Get source content
            source_text = source.assessment_text
            if not source_text:
                logger.warning(f"Source {source.id} has no content, skipping")
                progress.failed_assessments += 1
                continue

            try:
                # Assess the question
                answer = self.agent.assess_question(
                    source_content=source_text,
                    question=question,
                    source_title=source.title
                )

                # Store the result
                self.store_answer(source.id, answer, question)
                progress.completed_assessments += 1

            except Exception as e:
                logger.error(f"Assessment failed for source {source.id}, question {question.key}: {e}")
                progress.failed_assessments += 1

        # Final progress update
        progress.current_source = None
        progress.current_question = None
        if progress_callback:
            progress_callback(progress)

        logger.info(
            f"Assessment complete: {progress.completed_assessments} completed, "
            f"{progress.failed_assessments} failed"
        )

        return progress

    def run_single(self, source_id: int, question_key: str) -> Optional[Answer]:
        """
        Run assessment for a single source/question pair.

        Args:
            source_id: ID of the source
            question_key: Key of the question

        Returns:
            Answer if successful, None if failed
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, abstract, content
            FROM sources
            WHERE id = ?
        """, (source_id,))
        row = cursor.fetchone()

        if not row:
            logger.error(f"Source {source_id} not found")
            return None

        source = SourceData(
            id=row[0],
            title=row[1] or '',
            abstract=row[2] or '',
            content=row[3]
        )

        question = self.config.get_question(question_key)
        if not question:
            logger.error(f"Question '{question_key}' not found in config")
            return None

        source_text = source.assessment_text
        if not source_text:
            logger.error(f"Source {source_id} has no content")
            return None

        try:
            answer = self.agent.assess_question(
                source_content=source_text,
                question=question,
                source_title=source.title
            )
            self.store_answer(source_id, answer, question)
            return answer
        except Exception as e:
            logger.error(f"Assessment failed: {e}")
            return None


def get_matrix_data(conn: sqlite3.Connection, project_id: int) -> dict:
    """
    Load content matrix data for a project.

    Args:
        conn: Database connection
        project_id: Project ID

    Returns:
        Dictionary with structure:
        {
            'sources': [{id, title, ...}, ...],
            'questions': [key1, key2, ...],
            'matrix': {source_id: {question_key: {answer, confidence, ...}}}
        }
    """
    cursor = conn.cursor()

    # Get sources
    cursor.execute("""
        SELECT s.id, s.title, s.authors, s.year
        FROM sources s
        JOIN project_sources ps ON s.id = ps.source_id
        WHERE ps.project_id = ?
        ORDER BY s.id
    """, (project_id,))

    sources = []
    for row in cursor.fetchall():
        sources.append({
            'id': row[0],
            'title': row[1],
            'authors': row[2],
            'year': row[3]
        })

    # Get matrix entries
    cursor.execute("""
        SELECT source_id, question_key, answer, answer_type, confidence, citations
        FROM content_matrix
        WHERE project_id = ?
    """, (project_id,))

    matrix = {}
    questions = set()

    for row in cursor.fetchall():
        source_id, question_key, answer, answer_type, confidence, citations = row
        questions.add(question_key)

        if source_id not in matrix:
            matrix[source_id] = {}

        # Parse citations
        try:
            citations_data = json.loads(citations) if citations else []
        except json.JSONDecodeError:
            citations_data = []

        matrix[source_id][question_key] = {
            'answer': answer,
            'answer_type': answer_type,
            'confidence': confidence,
            'citations': citations_data
        }

    return {
        'sources': sources,
        'questions': sorted(questions),
        'matrix': matrix
    }


def clear_matrix(conn: sqlite3.Connection, project_id: int):
    """Clear all content matrix entries for a project."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM content_matrix WHERE project_id = ?", (project_id,))
    conn.commit()
    logger.info(f"Cleared content matrix for project {project_id}")
