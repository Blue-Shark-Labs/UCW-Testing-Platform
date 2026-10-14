# Create the PostgreSQL schema.
# Run with `make setup-db` (or `python3 -m database.migrations.migrate` from
# the project root
# Table/column names mirror the ERD, translated to snake_case (Postgressub
# lower-cases unquoted identifiers, so camelCase would require quoting
# every reference). The connection uses the DATABASE_URL/DATABASE_NAME/
# USERNAME/PASSWORD environment variables via the shared connection provider.

from database.connection import PostgresConnectionProvider

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        -- CHECK stands in for the ERD's ENUM(student, lecturer, admin); Postgres has
        -- no inline enum type, and a named enum would complicate future value changes.
        role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'lecturer', 'admin')),
        mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
        mfa_secret VARCHAR(64),
        is_disabled BOOLEAN NOT NULL DEFAULT FALSE,
        last_login_at TIMESTAMP DEFAULT NULL
    );
    """,
    # One-to-one extension of users for role='student' accounts.
    """
    CREATE TABLE IF NOT EXISTS students (
        user_id INT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
        student_number VARCHAR(20) NOT NULL,
        course_title VARCHAR(100) NOT NULL,
        is_approved BOOLEAN NOT NULL DEFAULT FALSE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description VARCHAR(250),
        is_active BOOLEAN NOT NULL DEFAULT TRUE
    );
    """,
    # Questions are drawn from the subject's question pool, not tied to a
    # specific test, so a test only records how many to present and for how long.
    """
    CREATE TABLE IF NOT EXISTS tests (
        test_id SERIAL PRIMARY KEY,
        subject_id INT NOT NULL REFERENCES subjects(subject_id),
        title VARCHAR(150) NOT NULL,
        question_count INT NOT NULL,
        time_limit_minutes INT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS questions (
        question_id SERIAL PRIMARY KEY,
        subject_id INT NOT NULL REFERENCES subjects(subject_id),
        question_text TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS answer_options (
        option_id SERIAL PRIMARY KEY,
        question_id INT NOT NULL REFERENCES questions(question_id),
        option_text VARCHAR(255) NOT NULL,
        is_correct BOOLEAN NOT NULL DEFAULT FALSE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS test_attempts (
        attempt_id SERIAL PRIMARY KEY,
        test_id INT NOT NULL REFERENCES tests(test_id),
        student_id INT NOT NULL REFERENCES users(user_id),
        completed_at TIMESTAMP,
        percentage DECIMAL(5, 2),
        total_points INT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS attempt_answers (
        answer_attempt_id SERIAL PRIMARY KEY,
        attempt_id INT NOT NULL REFERENCES test_attempts(attempt_id),
        question_id INT NOT NULL REFERENCES questions(question_id),
        selected_option_id INT NOT NULL REFERENCES answer_options(option_id),
        points_awarded INT CHECK (points_awarded IN (30, -10, 0))
    );
    """,
    # Indexes on foreign key columns (Postgres doesn't create these automatically).
    "CREATE INDEX IF NOT EXISTS idx_tests_subject_id ON tests(subject_id);",
    "CREATE INDEX IF NOT EXISTS idx_questions_subject_id ON questions(subject_id);",
    "CREATE INDEX IF NOT EXISTS idx_answer_options_question_id ON answer_options(question_id);",
    "CREATE INDEX IF NOT EXISTS idx_test_attempts_test_id ON test_attempts(test_id);",
    "CREATE INDEX IF NOT EXISTS idx_test_attempts_student_id ON test_attempts(student_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempt_answers_attempt_id ON attempt_answers(attempt_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempt_answers_question_id ON attempt_answers(question_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempt_answers_selected_option_id ON attempt_answers(selected_option_id);",
]


def migrate():
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        for statement in SCHEMA_STATEMENTS:
            cur.execute(statement)
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
