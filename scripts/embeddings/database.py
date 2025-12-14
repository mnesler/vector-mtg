"""
Database Operations for MTG Card Tag Extraction
================================================
Handles database interactions for tag loading and storage.

Extracted from: extract_card_tags.py
Refactoring Phase: 2
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict

from .models import CardTagExtraction

logger = logging.getLogger(__name__)


def get_default_db_connection_string() -> str:
    """
    Get default database connection string from environment variables.

    Returns:
        PostgreSQL connection string

    Example:
        >>> conn_str = get_default_db_connection_string()
        >>> # Returns: postgresql://postgres:postgres@localhost:5432/vector_mtg
    """
    return (
        f"postgresql://"
        f"{os.getenv('POSTGRES_USER', 'postgres')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'vector_mtg')}"
    )


def load_tag_taxonomy(db_conn_string: str) -> List[Dict]:
    """
    Load available tags from database with their metadata.

    Args:
        db_conn_string: PostgreSQL connection string

    Returns:
        List of tag dictionaries containing:
        - name: Tag identifier (e.g., "generates_mana")
        - display_name: Human-readable name
        - description: Tag description
        - category: Category name
        - is_combo_relevant: Boolean flag
        - depth: Hierarchy depth (0 = root)
        - parent_tag_id: UUID of parent tag (or None)
        - parent_tag_name: Name of parent tag (or None)

    Raises:
        psycopg2.Error: If database query fails

    Example:
        >>> tags = load_tag_taxonomy("postgresql://...")
        >>> len(tags)
        65
    """
    logger.info("Loading tag taxonomy from database...")

    with psycopg2.connect(db_conn_string) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    t.name,
                    t.display_name,
                    t.description,
                    tc.display_name as category,
                    t.is_combo_relevant,
                    t.depth,
                    t.parent_tag_id,
                    CASE
                        WHEN t.parent_tag_id IS NOT NULL THEN
                            (SELECT name FROM tags WHERE id = t.parent_tag_id)
                        ELSE NULL
                    END as parent_tag_name
                FROM tags t
                JOIN tag_categories tc ON t.category_id = tc.id
                ORDER BY tc.sort_order, t.depth, t.name
            """)

            tags = [dict(row) for row in cur.fetchall()]

    logger.info(f"Loaded {len(tags)} tags from database")
    return tags


def store_card_tags(
    extraction: CardTagExtraction,
    db_conn_string: str,
    llm_model: str,
    llm_provider: str = "unknown",
    extraction_prompt_version: str = "1.0"
) -> bool:
    """
    Store extracted tags in the database.

    The trigger `update_card_tag_cache_trigger` will automatically:
    - Update cards.tag_cache[]
    - Calculate cards.tag_confidence_avg
    - Add to review queue if confidence < 0.7

    Args:
        extraction: CardTagExtraction result with tags
        db_conn_string: PostgreSQL connection string
        llm_model: Model identifier (e.g., "claude-3-5-haiku-20241022")
        llm_provider: Provider name (e.g., "anthropic", "openai", "ollama")
        extraction_prompt_version: Version string for tracking prompt iterations

    Returns:
        True if successful, False otherwise

    Example:
        >>> extraction = CardTagExtraction(
        ...     card_id="abc-123",
        ...     card_name="Sol Ring",
        ...     tags=[TagResult(tag="artifact", confidence=1.0)],
        ...     extraction_successful=True
        ... )
        >>> store_card_tags(extraction, "postgresql://...", "claude-3-5-haiku-20241022", "anthropic")
        True
    """
    if not extraction.extraction_successful:
        logger.error(f"Cannot store tags for {extraction.card_name}: extraction failed")
        return False

    if not extraction.card_id:
        logger.error(f"Cannot store tags for {extraction.card_name}: no card_id provided")
        return False

    try:
        with psycopg2.connect(db_conn_string) as conn:
            with conn.cursor() as cur:
                # Delete existing tags for this card (for re-extraction)
                cur.execute(
                    "DELETE FROM card_tags WHERE card_id = %s",
                    (extraction.card_id,)
                )

                # Insert new tags
                for tag in extraction.tags:
                    cur.execute("""
                        INSERT INTO card_tags (
                            card_id,
                            tag_id,
                            confidence,
                            source,
                            llm_model,
                            llm_provider,
                            extraction_prompt_version,
                            extracted_at
                        )
                        SELECT
                            %s,
                            t.id,
                            %s,
                            'llm',
                            %s,
                            %s,
                            %s,
                            NOW()
                        FROM tags t
                        WHERE t.name = %s
                    """, (
                        extraction.card_id,
                        tag.confidence,
                        llm_model,
                        llm_provider,
                        extraction_prompt_version,
                        tag.tag
                    ))

                conn.commit()
                logger.info(f"Stored {len(extraction.tags)} tags for {extraction.card_name}")
                return True

    except Exception as e:
        logger.error(f"Failed to store tags for {extraction.card_name}: {e}")
        return False
