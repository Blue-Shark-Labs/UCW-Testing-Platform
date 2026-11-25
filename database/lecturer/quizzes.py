"""Queries for lecturer quiz and question pool management."""

from uuid import UUID

import psycopg

from database.connection import PostgresConnectionProvider


def list_subjects_with_pool_counts() -> list[dict]:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT
                s.subject_id,
                s.name,
                s.is_active,
                COUNT(q.question_id) AS question_count
            FROM subjects s
            LEFT JOIN questions q
                ON q.subject_id = s.subject_id
               AND q.is_deleted = FALSE
            GROUP BY s.subject_id, s.name, s.is_active
            ORDER BY s.name;
        """)
        return [
            {
                "subject_id": str(row[0]),
                "name": row[1],
                "is_active": bool(row[2]),
                "question_count": int(row[3]),
            }
            for row in cur.fetchall()
        ]


def get_subject_question_count(subject_id: UUID) -> int:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM questions
            WHERE subject_id = %s
              AND is_deleted = FALSE;
        """, (subject_id,))
        return int(cur.fetchone()[0])


def list_quizzes() -> list[dict]:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT
                t.test_id,
                t.subject_id,
                s.name AS subject_name,
                t.title,
                t.description,
                t.question_count,
                t.time_limit_minutes,
                t.is_active,
                COUNT(ta.attempt_id) AS attempt_count
            FROM tests t
            JOIN subjects s ON s.subject_id = t.subject_id
            LEFT JOIN test_attempts ta ON ta.test_id = t.test_id
            WHERE t.is_archived = FALSE
            GROUP BY
                t.test_id,
                t.subject_id,
                s.name,
                t.title,
                t.description,
                t.question_count,
                t.time_limit_minutes,
                t.is_active
            ORDER BY t.title;
        """)
        return [
            {
                "test_id": str(row[0]),
                "subject_id": str(row[1]),
                "subject_name": row[2],
                "title": row[3],
                "description": row[4] or "",
                "question_count": int(row[5]),
                "time_limit_minutes": row[6],
                "is_active": bool(row[7]),
                "attempt_count": int(row[8]),
            }
            for row in cur.fetchall()
        ]


def create_quiz(
    subject_id: UUID,
    created_by: UUID | None,
    title: str,
    description: str,
    question_count: int,
    time_limit_minutes: int | None,
) -> UUID:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM questions
            WHERE subject_id = %s
              AND is_deleted = FALSE;
        """, (subject_id,))
        available_count = int(cur.fetchone()[0])

        if question_count < 1 or question_count > available_count:
            raise ValueError(
                f"Question count must be between 1 and {available_count} "
                f"(available questions in this subject pool)."
            )

        cur.execute("""
            INSERT INTO tests (
                subject_id,
                created_by,
                title,
                description,
                question_count,
                time_limit_minutes,
                is_active,
                is_archived
            )
            VALUES (%s, %s, %s, %s, %s, %s, TRUE, FALSE)
            RETURNING test_id;
        """, (
            subject_id,
            created_by,
            title,
            description,
            question_count,
            time_limit_minutes,
        ))
        return cur.fetchone()[0]


def update_quiz(
    test_id: UUID,
    subject_id: UUID,
    title: str,
    description: str,
    question_count: int,
    time_limit_minutes: int | None,
) -> tuple[bool, str | None]:
    """Returns (True, None) on success or (False, error_message) on failure."""
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT
                t.subject_id,
                t.question_count,
                t.time_limit_minutes,
                COUNT(ta.attempt_id) AS attempt_count
            FROM tests t
            LEFT JOIN test_attempts ta ON ta.test_id = t.test_id
            WHERE t.test_id = %s
              AND t.is_archived = FALSE
            GROUP BY t.test_id, t.subject_id, t.question_count, t.time_limit_minutes;
        """, (test_id,))
        existing = cur.fetchone()
        if existing is None:
            return False, "Quiz not found."

        existing_subject_id, existing_q_count, existing_time_limit, attempt_count = existing

        # FR-76 / FR-77 / FR-78: Lock structural parameters once attempts exist.
        if int(attempt_count) > 0:
            if (
                subject_id != existing_subject_id
                or question_count != int(existing_q_count)
                or time_limit_minutes != existing_time_limit
            ):
                return (
                    False,
                    "This quiz has existing student attempts. Only the title and "
                    "description can be modified.",
                )

            cur.execute("""
                UPDATE tests
                SET title = %s,
                    description = %s
                WHERE test_id = %s
                  AND is_archived = FALSE;
            """, (title, description, test_id))
            return True, None

        cur.execute("""
            SELECT COUNT(*)
            FROM questions
            WHERE subject_id = %s
              AND is_deleted = FALSE;
        """, (subject_id,))
        available_count = int(cur.fetchone()[0])

        if question_count < 1 or question_count > available_count:
            return (
                False,
                f"Question count must be between 1 and {available_count} "
                f"(available questions in this subject pool).",
            )

        cur.execute("""
            UPDATE tests
            SET subject_id = %s,
                title = %s,
                description = %s,
                question_count = %s,
                time_limit_minutes = %s
            WHERE test_id = %s
              AND is_archived = FALSE;
        """, (
            subject_id,
            title,
            description,
            question_count,
            time_limit_minutes,
            test_id,
        ))
        return cur.rowcount > 0, None


def toggle_quiz_status(test_id: UUID) -> bool | None:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            UPDATE tests
            SET is_active = NOT is_active
            WHERE test_id = %s
              AND is_archived = FALSE
            RETURNING is_active;
        """, (test_id,))
        result = cur.fetchone()
        return bool(result[0]) if result is not None else None


def delete_quiz(test_id: UUID, confirmed_archive: bool) -> tuple[str, str | None]:
    """Returns ('not_found', None), ('requires_confirmation', title),
    ('archived', title), or ('deleted', title).
    """
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT
                t.title,
                COUNT(ta.attempt_id) AS attempt_count
            FROM tests t
            LEFT JOIN test_attempts ta ON ta.test_id = t.test_id
            WHERE t.test_id = %s
              AND t.is_archived = FALSE
            GROUP BY t.test_id, t.title;
        """, (test_id,))
        row = cur.fetchone()
        if row is None:
            return "not_found", None

        title, attempt_count = row[0], int(row[1])

        if attempt_count > 0:
            if not confirmed_archive:
                return "requires_confirmation", title

            cur.execute("""
                UPDATE tests
                SET is_archived = TRUE,
                    is_active = FALSE
                WHERE test_id = %s;
            """, (test_id,))
            return "archived", title

        cur.execute("""
            DELETE FROM tests
            WHERE test_id = %s;
        """, (test_id,))
        return "deleted", title


def list_questions() -> list[dict]:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT
                q.question_id,
                q.subject_id,
                s.name AS subject_name,
                q.question_text
            FROM questions q
            JOIN subjects s ON s.subject_id = q.subject_id
            WHERE q.is_deleted = FALSE
            ORDER BY s.name, q.question_id;
        """)
        question_rows = cur.fetchall()

        cur.execute("""
            SELECT
                ao.option_id,
                ao.question_id,
                ao.option_text,
                ao.is_correct
            FROM answer_options ao
            JOIN questions q ON q.question_id = ao.question_id
            WHERE q.is_deleted = FALSE
            ORDER BY ao.option_id;
        """)
        options_by_question: dict[str, list[dict]] = {}
        for opt_id, q_id, opt_text, is_correct in cur.fetchall():
            options_by_question.setdefault(str(q_id), []).append({
                "option_id": str(opt_id),
                "option_text": opt_text,
                "is_correct": bool(is_correct),
            })

        return [
            {
                "question_id": str(row[0]),
                "subject_id": str(row[1]),
                "subject_name": row[2],
                "question_text": row[3],
                "options": options_by_question.get(str(row[0]), []),
            }
            for row in question_rows
        ]


def create_question(
    subject_id: UUID,
    question_text: str,
    options: list[tuple[str, bool]],
) -> UUID:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            INSERT INTO questions (subject_id, question_text, is_deleted)
            VALUES (%s, %s, FALSE)
            RETURNING question_id;
        """, (subject_id, question_text))
        question_id = cur.fetchone()[0]

        for option_text, is_correct in options:
            cur.execute("""
                INSERT INTO answer_options (question_id, option_text, is_correct)
                VALUES (%s, %s, %s);
            """, (question_id, option_text, is_correct))

        return question_id


def update_question(
    question_id: UUID,
    subject_id: UUID,
    question_text: str,
    options: list[tuple[str, bool]],
) -> bool:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            UPDATE questions
            SET subject_id = %s,
                question_text = %s
            WHERE question_id = %s
              AND is_deleted = FALSE
            RETURNING question_id;
        """, (subject_id, question_text, question_id))
        if cur.fetchone() is None:
            return False

        cur.execute("""
            SELECT option_id
            FROM answer_options
            WHERE question_id = %s
            ORDER BY option_id;
        """, (question_id,))
        existing_option_ids = [row[0] for row in cur.fetchall()]

        # Update existing option rows in-place first to preserve foreign keys in attempt_answers
        for idx, (option_text, is_correct) in enumerate(options):
            if idx < len(existing_option_ids):
                cur.execute("""
                    UPDATE answer_options
                    SET option_text = %s,
                        is_correct = %s
                    WHERE option_id = %s;
                """, (option_text, is_correct, existing_option_ids[idx]))
            else:
                cur.execute("""
                    INSERT INTO answer_options (question_id, option_text, is_correct)
                    VALUES (%s, %s, %s);
                """, (question_id, option_text, is_correct))

        # Remove any surplus trailing options if unreferenced
        for extra_option_id in existing_option_ids[len(options):]:
            try:
                cur.execute("SAVEPOINT sp_del_opt;")
                cur.execute(
                    "DELETE FROM answer_options WHERE option_id = %s;",
                    (extra_option_id,),
                )
                cur.execute("RELEASE SAVEPOINT sp_del_opt;")
            except psycopg.errors.ForeignKeyViolation:
                cur.execute("ROLLBACK TO SAVEPOINT sp_del_opt;")

        return True


def delete_question(question_id: UUID) -> bool:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            UPDATE questions
            SET is_deleted = TRUE
            WHERE question_id = %s
              AND is_deleted = FALSE
            RETURNING question_id;
        """, (question_id,))
        return cur.fetchone() is not None

def get_quiz_statistics(test_id: UUID) -> dict | None:
    """FR-75: Returns summary metrics and completed attempt records for a quiz."""
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT
                t.test_id,
                t.title,
                t.description,
                s.name AS subject_name,
                t.question_count,
                t.time_limit_minutes,
                t.is_active
            FROM tests t
            JOIN subjects s ON s.subject_id = t.subject_id
            WHERE t.test_id = %s
              AND t.is_archived = FALSE;
        """, (test_id,))
        quiz_row = cur.fetchone()
        if quiz_row is None:
            return None

        cur.execute("""
            SELECT
                ta.attempt_id,
                u.first_name,
                u.last_name,
                COALESCE(st.student_number, 'N/A'),
                ta.completed_at,
                ta.percentage,
                ta.total_points
            FROM test_attempts ta
            JOIN users u ON u.user_id = ta.user_id
            LEFT JOIN students st ON st.user_id = u.user_id
            WHERE ta.test_id = %s
              AND ta.completed_at IS NOT NULL
            ORDER BY ta.completed_at DESC;
        """, (test_id,))
        attempts = [
            {
                "attempt_id": str(row[0]),
                "student_name": f"{row[1]} {row[2]}".strip(),
                "student_number": row[3],
                "completed_at": row[4].strftime("%d %b %Y, %H:%M") if row[4] else "In Progress",
                "percentage": float(row[5]) if row[5] is not None else 0.0,
                "total_points": int(row[6]) if row[6] is not None else 0,
            }
            for row in cur.fetchall()
        ]

        completed_count = len(attempts)
        avg_percentage = (
            round(sum(a["percentage"] for a in attempts) / completed_count, 1)
            if completed_count > 0
            else None
        )
        avg_points = (
            round(sum(a["total_points"] for a in attempts) / completed_count, 1)
            if completed_count > 0
            else None
        )
        highest_percentage = max((a["percentage"] for a in attempts), default=None)
        lowest_percentage = min((a["percentage"] for a in attempts), default=None)

        return {
            "quiz": {
                "test_id": str(quiz_row[0]),
                "title": quiz_row[1],
                "description": quiz_row[2] or "",
                "subject_name": quiz_row[3],
                "question_count": int(quiz_row[4]),
                "time_limit_minutes": quiz_row[5],
                "is_active": bool(quiz_row[6]),
            },
            "summary": {
                "completed_count": completed_count,
                "avg_percentage": avg_percentage,
                "avg_points": avg_points,
                "highest_percentage": highest_percentage,
                "lowest_percentage": lowest_percentage,
            },
            "attempts": attempts,
        }