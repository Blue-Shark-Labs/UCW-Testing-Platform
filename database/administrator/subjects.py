"""Queries for administrator subject management."""

from uuid import UUID

from database.connection import PostgresConnectionProvider


def _format_subject(row: tuple) -> dict:
    return {
        "subjectId": str(row[0]),
        "name": row[1],
        "description": row[2],
        "isActive": row[3],
        "lecturerNames": row[4] if len(row) > 4 else [],
    }


def _validate_lecturer_ids(cur, lecturer_ids: list[UUID]) -> None:
    if not lecturer_ids:
        return

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ANY(%s)
          AND role IN ('lecturer', 'admin');
        """,
        (lecturer_ids,),
    )
    valid_ids = {row[0] for row in cur.fetchall()}
    if valid_ids != set(lecturer_ids):
        raise ValueError("One or more selected lecturers are unavailable.")


def list_subjects(search: str, limit: int, offset: int) -> tuple[list[dict], int]:
    pattern = f"%{search}%"
    provider = PostgresConnectionProvider()

    with provider.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM subjects
            WHERE %s = ''
               OR name ILIKE %s
               OR COALESCE(description, '') ILIKE %s;
            """,
            (search, pattern, pattern),
        )
        total = cur.fetchone()[0]

        cur.execute(
            """
            SELECT
                s.subject_id,
                s.name,
                s.description,
                s.is_active,
                COALESCE(
                    array_agg(u.first_name || ' ' || u.last_name ORDER BY u.last_name, u.first_name)
                        FILTER (WHERE u.user_id IS NOT NULL),
                    ARRAY[]::text[]
                ) AS lecturer_names
            FROM subjects AS s
            LEFT JOIN subject_lecturers AS sl ON sl.subject_id = s.subject_id
            LEFT JOIN users AS u ON u.user_id = sl.user_id
            WHERE %s = ''
               OR s.name ILIKE %s
               OR COALESCE(s.description, '') ILIKE %s
            GROUP BY s.subject_id
            ORDER BY LOWER(s.name), s.subject_id
            LIMIT %s OFFSET %s;
            """,
            (search, pattern, pattern, limit, offset),
        )
        subjects = [_format_subject(row) for row in cur.fetchall()]

    return subjects, total


def get_subject(subject_id: UUID) -> dict | None:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute(
            """
            SELECT subject_id, name, description, is_active
            FROM subjects
            WHERE subject_id = %s;
            """,
            (subject_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        subject = _format_subject(row)
        cur.execute(
            """
            SELECT u.user_id, u.first_name, u.last_name
            FROM subject_lecturers AS sl
            JOIN users AS u ON u.user_id = sl.user_id
            WHERE sl.subject_id = %s
            ORDER BY u.last_name, u.first_name;
            """,
            (subject_id,),
        )
        subject["lecturers"] = [
            {
                "userId": str(lecturer[0]),
                "firstName": lecturer[1],
                "lastName": lecturer[2],
            }
            for lecturer in cur.fetchall()
        ]
    return subject


def list_available_lecturers() -> list[dict]:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, first_name, last_name
            FROM users
            WHERE role IN ('lecturer', 'admin')
            ORDER BY last_name, first_name;
            """
        )
        return [
            {
                "userId": str(row[0]),
                "firstName": row[1],
                "lastName": row[2],
            }
            for row in cur.fetchall()
        ]


def create_subject(
    name: str,
    description: str,
    lecturer_ids: list[UUID],
    subject_id: UUID,
) -> UUID:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        _validate_lecturer_ids(cur, lecturer_ids)
        cur.execute(
            """
            INSERT INTO subjects (subject_id, name, description, is_active)
            VALUES (%s, %s, %s, TRUE)
            RETURNING subject_id;
            """,
            (subject_id, name, description),
        )
        subject_id = cur.fetchone()[0]
        for lecturer_id in lecturer_ids:
            cur.execute(
                """
                INSERT INTO subject_lecturers (subject_id, user_id)
                VALUES (%s, %s);
                """,
                (subject_id, lecturer_id),
            )
    return subject_id


def update_subject(
    subject_id: UUID,
    name: str,
    description: str,
    is_active: bool,
    lecturer_ids: list[UUID],
) -> bool:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        _validate_lecturer_ids(cur, lecturer_ids)
        cur.execute(
            """
            UPDATE subjects
            SET name = %s, description = %s, is_active = %s
            WHERE subject_id = %s;
            """,
            (name, description, is_active, subject_id),
        )
        if cur.rowcount == 0:
            return False

        cur.execute(
            "DELETE FROM subject_lecturers WHERE subject_id = %s;",
            (subject_id,),
        )
        for lecturer_id in lecturer_ids:
            cur.execute(
                """
                INSERT INTO subject_lecturers (subject_id, user_id)
                VALUES (%s, %s);
                """,
                (subject_id, lecturer_id),
            )
    return True
