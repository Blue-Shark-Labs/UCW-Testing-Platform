"""Queries for read-only lecturer subject views."""

from uuid import UUID

from database.connection import PostgresConnectionProvider

def list_lecturer_subjects(lecturer_id: UUID | str, search: str = "", assigned_only: bool = False) -> list[dict]:
    """Return subjects visible to the lecturer, optionally restricted to assigned ones."""
    pattern = f"%{search.strip()}%"
    provider = PostgresConnectionProvider()

    with provider.cursor() as cur:
        cur.execute(
            """
            SELECT
                s.subject_id,
                s.name,
                COALESCE(s.description, '') AS description,
                s.is_active,
                (sl_me.user_id IS NOT NULL) AS is_assigned,
                COALESCE(
                    (
                        SELECT array_agg(
                            u.first_name || ' ' || u.last_name
                            ORDER BY u.last_name, u.first_name
                        )
                        FROM subject_lecturers AS sl_all
                        JOIN users AS u ON u.user_id = sl_all.user_id
                        WHERE sl_all.subject_id = s.subject_id
                    ),
                    ARRAY[]::text[]
                ) AS lecturer_names,
                (
                    SELECT COUNT(*)
                    FROM questions AS qp
                    WHERE qp.subject_id = s.subject_id
                      AND qp.is_deleted = FALSE
                ) AS question_count,
                (
                    SELECT COUNT(*)
                    FROM tests AS t
                    WHERE t.subject_id = s.subject_id
                ) AS quiz_count
            FROM subjects AS s
            LEFT JOIN subject_lecturers AS sl_me
              ON sl_me.subject_id = s.subject_id
             AND sl_me.user_id = %s
            WHERE (%s = FALSE OR sl_me.user_id IS NOT NULL)
              AND (%s = ''
               OR s.name ILIKE %s
               OR COALESCE(s.description, '') ILIKE %s)
            ORDER BY is_assigned DESC, s.is_active DESC, LOWER(s.name), s.subject_id;
            """,
            (str(lecturer_id), assigned_only, search.strip(), pattern, pattern),
        )
        rows = cur.fetchall()

    return [
        {
            "subject_id": str(row[0]),
            "name": row[1],
            "description": row[2],
            "is_active": bool(row[3]),
            "is_assigned": bool(row[4]),
            "lecturer_names": row[5] or [],
            "question_count": int(row[6] or 0),
            "quiz_count": int(row[7] or 0),
        }
        for row in rows
    ]