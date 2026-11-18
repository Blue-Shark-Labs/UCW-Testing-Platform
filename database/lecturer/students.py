"""Queries for lecturer student management."""

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
            ORDER BY u.last_name, u.first_name;
        """)
        return cur.fetchall()


def approve_student(student_id: UUID) -> bool:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            UPDATE students
            SET is_approved = TRUE
            WHERE user_id = %s
            RETURNING user_id;
        """, (student_id,))
        return cur.fetchone() is not None


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
    """Returns ('has_attempts', None), ('not_found', None), or ('deleted', (first_name, last_name))."""
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM test_attempts
                WHERE user_id = %s
            );
        """, (student_id,))
        if cur.fetchone()[0]:
            return "has_attempts", None

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