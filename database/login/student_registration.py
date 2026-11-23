# Persistence for self-registered student accounts.

from dataclasses import dataclass

from psycopg.errors import UniqueViolation


@dataclass(frozen=True)
class StudentRegistration:
    first_name: str
    last_name: str
    email: str
    student_number: str
    course_title: str
    password: str


STUDENT_NUMBER_CONSTRAINT = "idx_students_student_number"


class DuplicateStudentNumberError(Exception):
    """Raised when the student number is already registered."""


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
        try:
            cur.execute(INSERT_STUDENT, (row[0], registration.student_number, registration.course_title))
        except UniqueViolation as e:
            # Raising inside the cursor block rolls back the users insert too.
            if e.diag.constraint_name == STUDENT_NUMBER_CONSTRAINT:
                raise DuplicateStudentNumberError() from e
            raise
    return True
