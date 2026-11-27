"""Queries for administrator user management."""

from uuid import UUID

from database.connection import PostgresConnectionProvider


def _format_user(row: tuple) -> dict:
    last_login = row[8] if len(row) > 8 else None
    return {
        "userId": str(row[0]),
        "firstName": row[1],
        "lastName": row[2],
        "email": row[3],
        "role": row[4],
        "isDisabled": row[5],
        "lastLoginAt": last_login.isoformat(sep=" ", timespec="seconds")
        if last_login
        else "",
        "studentNumber": row[6] if len(row) > 6 else "",
        "courseTitle": row[7] if len(row) > 7 else "",
    }


def list_users(search: str, limit: int, offset: int) -> tuple[list[dict], int]:
    pattern = f"%{search}%"
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE role IN ('lecturer', 'admin')
              AND (
                    %s = ''
                    OR first_name ILIKE %s
                    OR last_name ILIKE %s
                    OR email ILIKE %s
              );
            """,
            (search, pattern, pattern, pattern),
        )
        total = cur.fetchone()[0]
        cur.execute(
            """
            SELECT
                u.user_id, u.first_name, u.last_name, u.email, u.role,
                u.is_disabled, s.student_number, s.course_title, u.last_login_at
            FROM users AS u
            LEFT JOIN students AS s ON s.user_id = u.user_id
            WHERE u.role IN ('lecturer', 'admin')
              AND (
                    %s = ''
                    OR u.first_name ILIKE %s
                    OR u.last_name ILIKE %s
                    OR u.email ILIKE %s
              )
            ORDER BY LOWER(u.last_name), LOWER(u.first_name), u.user_id
            LIMIT %s OFFSET %s;
            """,
            (search, pattern, pattern, pattern, limit, offset),
        )
        users = [_format_user(row) for row in cur.fetchall()]
    return users, total


def get_user(user_id: UUID) -> dict | None:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute(
            """
            SELECT
                u.user_id, u.first_name, u.last_name, u.email, u.role,
                u.is_disabled, s.student_number, s.course_title, u.last_login_at
            FROM users AS u
            LEFT JOIN students AS s ON s.user_id = u.user_id
            WHERE u.user_id = %s;
            """,
            (user_id,),
        )
        row = cur.fetchone()
    return _format_user(row) if row else None


def create_user(
    first_name: str,
    last_name: str,
    email: str,
    password_hash: str,
    role: str,
    student_number: str | None,
    course_title: str | None,
) -> UUID:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (
                first_name, last_name, email, password_hash, role, is_disabled
            )
            VALUES (%s, %s, %s, %s, %s, TRUE)
            RETURNING user_id;
            """,
            (first_name, last_name, email, password_hash, role),
        )
        user_id = cur.fetchone()[0]
        if role == "student":
            cur.execute(
                """
                INSERT INTO students (user_id, student_number, course_title)
                VALUES (%s, %s, %s);
                """,
                (user_id, student_number, course_title),
            )
    return user_id


def update_user(
    user_id: UUID,
    first_name: str,
    last_name: str,
    email: str,
    role: str,
    student_number: str | None,
    course_title: str | None,
    password_hash: str | None = None,
) -> bool:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET first_name = %s, last_name = %s, email = %s, role = %s,
                password_hash = COALESCE(%s, password_hash)
            WHERE user_id = %s;
            """,
            (first_name, last_name, email, role, password_hash, user_id),
        )
        if cur.rowcount == 0:
            return False

        if role == "student":
            cur.execute(
                """
                INSERT INTO students (user_id, student_number, course_title)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    student_number = EXCLUDED.student_number,
                    course_title = EXCLUDED.course_title;
                """,
                (user_id, student_number, course_title),
            )
        else:
            cur.execute("DELETE FROM students WHERE user_id = %s;", (user_id,))
    return True


def set_user_disabled(user_id: UUID, is_disabled: bool) -> bool:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute(
            "UPDATE users SET is_disabled = %s WHERE user_id = %s;",
            (is_disabled, user_id),
        )
        return cur.rowcount > 0


def delete_user(user_id: UUID) -> bool:
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute("DELETE FROM users WHERE user_id = %s;", (user_id,))
        return cur.rowcount > 0
