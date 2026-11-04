# Persistence for self-registered student accounts.

INSERT_USER = """
    INSERT INTO users (first_name, last_name, email, password_hash, role)
    VALUES (%s, %s, %s, %s, 'student')
    ON CONFLICT (email) DO NOTHING
    RETURNING user_id;
"""

# is_approved is set explicitly so a lecturer must approve before the student can sign in (FR-14).
INSERT_STUDENT = """
    INSERT INTO students (user_id, student_number, course_title, is_approved)
    VALUES (%s, %s, %s, FALSE);
"""


def create_student(connection_provider, registration, password_hash):
    """Inserts an unapproved student. Returns False if the email is already registered."""
    with connection_provider.cursor() as cur:
        cur.execute(
            INSERT_USER,
            (
                registration.first_name,
                registration.last_name,
                registration.email,
                password_hash,
            ),
        )
        row = cur.fetchone()
        if row is None:
            return False
        cur.execute(INSERT_STUDENT, (row[0], registration.student_number, registration.course_title))
    return True
