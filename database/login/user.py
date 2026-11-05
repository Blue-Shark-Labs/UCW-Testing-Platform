# Query functions for the users table (login authentication).

from database.helpers.database_helpers import row_to_user

SELECT_USER_BY_EMAIL = """
    SELECT u.user_id, u.email, u.password_hash, u.role, u.is_disabled,
           COALESCE(s.is_approved, TRUE)
    FROM users u
    LEFT JOIN students s ON s.user_id = u.user_id
    WHERE u.email = %s;
"""


def get_user_by_email(connection_provider, email):
    """Fetches the user with the given email, or None if no such user exists."""
    with connection_provider.cursor() as cur:
        cur.execute(SELECT_USER_BY_EMAIL, (email,))
        row = cur.fetchone()
    if row is None:
        return None
    return row_to_user(row)
