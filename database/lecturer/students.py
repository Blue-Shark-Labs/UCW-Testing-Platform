"""Queries for lecturer student management and progress reporting."""

from uuid import UUID

from database.connection import PostgresConnectionProvider


def list_students() -> list[tuple]:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                u.last_login_at,
                u.is_disabled,
                s.student_number,
                s.course_title,
                s.is_approved
            FROM users u
            LEFT JOIN students s ON u.user_id = s.user_id
            WHERE u.role = 'student'
              AND u.email NOT LIKE 'deleted_%%@anonymised.local'
            ORDER BY u.last_name, u.first_name;
        """)
        return cur.fetchall()


def approve_student(student_id: UUID) -> dict | None:
    """Approves a pending student registration and returns their contact details."""
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            UPDATE students s
            SET is_approved = TRUE
            FROM users u
            WHERE s.user_id = u.user_id
              AND s.user_id = %s
              AND u.role = 'student'
            RETURNING u.email, u.first_name, u.last_name;
        """, (student_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "email": row[0],
            "first_name": row[1],
            "last_name": row[2],
        }


def reject_student(student_id: UUID) -> tuple[str, tuple[str, str] | None]:
    """Rejects a pending student registration (FR-56).

    Returns ('not_found', None), ('already_approved', None), or ('rejected', (first_name, last_name)).
    """
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT u.first_name, u.last_name, COALESCE(s.is_approved, FALSE)
            FROM users u
            LEFT JOIN students s ON s.user_id = u.user_id
            WHERE u.user_id = %s
              AND u.role = 'student';
        """, (student_id,))
        row = cur.fetchone()
        if row is None:
            return "not_found", None

        first_name, last_name, is_approved = row
        if is_approved:
            return "already_approved", None

        cur.execute("""
            DELETE FROM users
            WHERE user_id = %s
              AND role = 'student'
            RETURNING first_name, last_name;
        """, (student_id,))
        deleted = cur.fetchone()
        if deleted is None:
            return "not_found", None
        return "rejected", deleted


def toggle_student_status(student_id: UUID) -> bool | None:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            UPDATE users
            SET is_disabled = NOT is_disabled
            WHERE user_id = %s
              AND role = 'student'
            RETURNING is_disabled;
        """, (student_id,))
        result = cur.fetchone()
        return result[0] if result is not None else None


def update_student(student_id: UUID, first_name: str, last_name: str, course: str) -> bool:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            UPDATE users
            SET first_name = %s,
                last_name = %s
            WHERE user_id = %s
              AND role = 'student'
            RETURNING user_id;
        """, (first_name, last_name, student_id))

        if cur.fetchone() is None:
            return False

        cur.execute("""
            INSERT INTO students (
                user_id,
                student_number,
                course_title
            )
            VALUES (
                %s,
                'S' || LPAD(nextval('student_number_seq')::TEXT, 7, '0'),
                %s
            )
            ON CONFLICT (user_id)
            DO UPDATE SET course_title = EXCLUDED.course_title;
        """, (student_id, course))
        return True


def create_student(
    first_name: str,
    last_name: str,
    email: str,
    password_hash: str,
    course: str,
) -> str:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            INSERT INTO users (
                first_name,
                last_name,
                email,
                password_hash,
                role,
                is_disabled
            )
            VALUES (%s, %s, %s, %s, 'student', FALSE)
            RETURNING user_id;
        """, (first_name, last_name, email, password_hash))
        user_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO students (
                user_id,
                student_number,
                course_title,
                is_approved
            )
            VALUES (
                %s,
                'S' || LPAD(nextval('student_number_seq')::TEXT, 7, '0'),
                %s,
                TRUE
            )
            RETURNING student_number;
        """, (user_id, course))
        return cur.fetchone()[0]


def delete_student(student_id: UUID) -> tuple[str, tuple[str, str] | None]:
    """Terminates a student account in compliance with GDPR (NFR-05).

    If test attempts exist, scrubs PII and disables the account while preserving
    anonymised attempt history. Otherwise deletes the user record cleanly.
    Returns ('not_found', None), ('anonymised', (first_name, last_name)),
    or ('deleted', (first_name, last_name)).
    """
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT first_name, last_name
            FROM users
            WHERE user_id = %s
              AND role = 'student';
        """, (student_id,))
        user_row = cur.fetchone()
        if user_row is None:
            return "not_found", None

        original_name = (user_row[0], user_row[1])

        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM test_attempts
                WHERE user_id = %s
            );
        """, (student_id,))
        has_attempts = bool(cur.fetchone()[0])

        if has_attempts:
            anonymised_email = f"deleted_{str(student_id)[:24]}@anonymised.local"
            anonymised_number = f"ANON-{str(student_id)[:8].upper()}"

            cur.execute("""
                DELETE FROM test_assignments
                WHERE student_id = %s;
            """, (student_id,))

            cur.execute("""
                UPDATE users
                SET first_name = 'Deleted',
                    last_name = 'Student',
                    email = %s,
                    password_hash = '!ANONYMISED!',
                    is_disabled = TRUE,
                    mfa_enabled = FALSE,
                    mfa_secret = NULL
                WHERE user_id = %s
                  AND role = 'student';
            """, (anonymised_email, student_id))

            cur.execute("""
                UPDATE students
                SET student_number = %s,
                    course_title = 'Anonymised'
                WHERE user_id = %s;
            """, (anonymised_number, student_id))

            return "anonymised", original_name

        cur.execute("""
            DELETE FROM users
            WHERE user_id = %s
              AND role = 'student'
            RETURNING first_name, last_name;
        """, (student_id,))
        deleted_user = cur.fetchone()
        if not deleted_user:
            return "not_found", None
        return "deleted", deleted_user


def get_class_progress_summary() -> list[dict]:
    """FR-63: Aggregate class list with cumulative points and average percentages."""
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                COALESCE(s.student_number, 'Not assigned') AS student_number,
                COALESCE(s.course_title, 'Not assigned') AS course_title,
                COUNT(ta.attempt_id) AS completed_tests,
                COALESCE(SUM(ta.total_points), 0) AS cumulative_points,
                ROUND(AVG(ta.percentage), 1) AS average_percentage
            FROM users u
            JOIN students s ON s.user_id = u.user_id
            LEFT JOIN test_attempts ta
                ON ta.user_id = u.user_id
               AND ta.completed_at IS NOT NULL
            WHERE u.role = 'student'
              AND s.is_approved = TRUE
              AND u.email NOT LIKE 'deleted_%%@anonymised.local'
            GROUP BY
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                s.student_number,
                s.course_title
            ORDER BY cumulative_points DESC, average_percentage DESC NULLS LAST, u.last_name, u.first_name;
        """)
        return [
            {
                "student_id": str(row[0]),
                "first_name": row[1],
                "last_name": row[2],
                "name": f"{row[1]} {row[2]}".strip(),
                "email": row[3],
                "student_number": row[4],
                "course_title": row[5],
                "completed_tests": int(row[6]),
                "cumulative_points": int(row[7]),
                "average_percentage": float(row[8]) if row[8] is not None else None,
            }
            for row in cur.fetchall()
        ]


def get_student_progress_detail(student_id: UUID) -> dict | None:
    """FR-64 & FR-65: Student profile, detailed test history, and chronological trajectory."""
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT
                u.user_id,
                u.first_name,
                u.last_name,
                u.email,
                COALESCE(s.student_number, 'Not assigned'),
                COALESCE(s.course_title, 'Not assigned')
            FROM users u
            LEFT JOIN students s ON s.user_id = u.user_id
            WHERE u.user_id = %s
              AND u.role = 'student';
        """, (student_id,))
        student_row = cur.fetchone()
        if student_row is None:
            return None

        cur.execute("""
            SELECT
                ta.attempt_id,
                t.test_id,
                t.title AS test_name,
                sub.name AS subject_name,
                ta.completed_at,
                t.question_count,
                ta.percentage,
                ta.total_points
            FROM test_attempts ta
            JOIN tests t ON t.test_id = ta.test_id
            JOIN subjects sub ON sub.subject_id = t.subject_id
            WHERE ta.user_id = %s
              AND ta.completed_at IS NOT NULL
            ORDER BY ta.completed_at ASC;
        """, (student_id,))
        chronological_attempts = [
            {
                "attempt_id": str(row[0]),
                "test_id": str(row[1]),
                "test_name": row[2],
                "subject_name": row[3],
                "completed_at": row[4],
                "completed_date_str": row[4].strftime("%d %b %Y, %H:%M") if row[4] else "N/A",
                "short_date_str": row[4].strftime("%d %b") if row[4] else "N/A",
                "question_count": int(row[5]),
                "percentage": float(row[6]) if row[6] is not None else 0.0,
                "total_points": int(row[7]) if row[7] is not None else 0,
            }
            for row in cur.fetchall()
        ]

        total_completed = len(chronological_attempts)
        cumulative_points = sum(a["total_points"] for a in chronological_attempts)
        average_percentage = (
            round(sum(a["percentage"] for a in chronological_attempts) / total_completed, 1)
            if total_completed > 0
            else None
        )

        return {
            "student": {
                "student_id": str(student_row[0]),
                "name": f"{student_row[1]} {student_row[2]}".strip(),
                "email": student_row[3],
                "student_number": student_row[4],
                "course_title": student_row[5],
                "completed_tests": total_completed,
                "cumulative_points": cumulative_points,
                "average_percentage": average_percentage,
            },
            "trajectory": chronological_attempts,
            "history": list(reversed(chronological_attempts)),
        }