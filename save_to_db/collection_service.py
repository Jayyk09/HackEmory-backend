"""Collection service for grouping related videos."""

from typing import Optional, Dict, List
from db import get_db_conn


def create_collection(
    user_id: int,
    collection_title: str,
) -> int:
    """
    Create a new collection.

    Args:
        user_id: The user who owns this collection
        collection_title: Title for the collection

    Returns:
        The new collection id
    """
    conn = get_db_conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO collections (user_id, collection_title)
                VALUES (%s, %s)
                RETURNING id;
                """,
                (user_id, collection_title),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("INSERT INTO collections RETURNING id returned no row")
            collection_id = row[0]
            return int(collection_id)
    finally:
        conn.close()


def get_collection(collection_id: int) -> Optional[Dict]:
    """
    Get collection by ID.

    Returns:
        Collection dict with id, user_id, collection_title, created_at
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, collection_title, created_at
                FROM collections
                WHERE id = %s
                """,
                (collection_id,),
            )
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "user_id": row[1],
                    "collection_title": row[2],
                    "created_at": row[3],
                }
            return None
    finally:
        conn.close()


def get_user_collections(
    user_id: int,
    offset: int = 0,
    limit: int = 10,
) -> List[Dict]:
    """
    Get all collections for a user.

    Returns:
        List of collection dicts, ordered by newest first
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, collection_title, created_at
                FROM collections
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                OFFSET %s
                LIMIT %s
                """,
                (user_id, offset, limit),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "collection_title": row[2],
                    "created_at": row[3],
                }
                for row in rows
            ]
    finally:
        conn.close()


def generate_collection_title(subtopic_titles: List[str]) -> str:
    """
    Generate a collection title from subtopic titles.

    Args:
        subtopic_titles: List of subtopic titles

    Returns:
        A generated collection title
    """
    if not subtopic_titles:
        return "Untitled Collection"
    
    # If there's only one subtopic, use it directly
    if len(subtopic_titles) == 1:
        return subtopic_titles[0]
    
    # If there are 2-3 subtopics, join them with " & "
    if len(subtopic_titles) <= 3:
        return " & ".join(subtopic_titles)
    
    # If there are more than 3, use the first two and add "& More"
    return f"{subtopic_titles[0]} & {subtopic_titles[1]} & More"
