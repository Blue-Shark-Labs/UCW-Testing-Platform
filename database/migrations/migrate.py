# Create the PostgreSQL schema.
# Run with `make setup-db` (or `python3 -m database.migrations.migrate` from
# the project root).

# Table/column names mirror the ERD, translated to snake_case (Postgres
# lower-cases unquoted identifiers, so camelCase would require quoting
# every reference). The connection uses the DATABASE_URL/DATABASE_NAME/
# DATABASE_USER/PASSWORD environment variables via the shared connection provider.

from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        -- UNIQUE beyond the ERD since email is the login identifier.
        email VARCHAR(50) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        -- CHECK stands in for the ERD's ENUM(student, lecturer, admin); Postgres has
        -- no inline enum type, and a named enum would complicate future value changes.
        role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'lecturer', 'admin')),
        mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
        mfa_secret VARCHAR(64),
        is_disabled BOOLEAN NOT NULL DEFAULT FALSE,
        last_login_at TIMESTAMP DEFAULT NULL,
        failed_login_attempts INT NOT NULL DEFAULT 0,
        locked_until TIMESTAMP DEFAULT NULL
    );
    """,
    # Backfills the lockout columns on databases created before they existed.
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INT NOT NULL DEFAULT 0;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP DEFAULT NULL;",
    # One-to-one extension of users for role='student' accounts.
    """
    CREATE TABLE IF NOT EXISTS students (
        user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
        student_number VARCHAR(20) NOT NULL,
        course_title VARCHAR(100) NOT NULL,
        is_approved BOOLEAN NOT NULL DEFAULT FALSE
    );
    """,
    # Automatically generate student numbers.
    """
    CREATE SEQUENCE IF NOT EXISTS student_number_seq;
    """,
    # Initialise the sequence without moving it backwards.
    """
    SELECT setval(
        'student_number_seq',
        GREATEST(
            (SELECT last_value FROM student_number_seq),
            COALESCE(
                (
                    SELECT MAX(
                        CAST(SUBSTRING(student_number FROM 2) AS BIGINT)
                    )
                    FROM students
                    WHERE student_number ~ '^S[0-9]+$'
                ),
                1
            )
        ),
        TRUE
    );
    """,
    # Prevent duplicate student numbers.
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_students_student_number
    ON students(student_number);
    """,
    # Create subjects table
    """
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) NOT NULL,
        description VARCHAR(250),
        is_active BOOLEAN NOT NULL DEFAULT TRUE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS subject_lecturers (
        subject_id UUID NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
        user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        PRIMARY KEY (subject_id, user_id)
    );
    """,
    # Questions are drawn from the subject's question pool, not tied to a
    # specific test, so a test only records how many to present and for how long.
    """
    CREATE TABLE IF NOT EXISTS tests (
        test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        subject_id UUID NOT NULL REFERENCES subjects(subject_id),
        created_by UUID REFERENCES users(user_id),
        title VARCHAR(150) NOT NULL,
        question_count INT NOT NULL,
        time_limit_minutes INT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS test_assignments (
        assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        test_id UUID NOT NULL REFERENCES tests(test_id) ON DELETE CASCADE,
        student_id UUID NOT NULL REFERENCES students(user_id) ON DELETE CASCADE,
        assigned_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
        assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (test_id, student_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS questions (
        question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        subject_id UUID NOT NULL REFERENCES subjects(subject_id),
        question_text TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS answer_options (
        option_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        question_id UUID NOT NULL REFERENCES questions(question_id),
        option_text VARCHAR(255) NOT NULL,
        is_correct BOOLEAN NOT NULL DEFAULT FALSE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS test_attempts (
        attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        test_id UUID NOT NULL REFERENCES tests(test_id),
        user_id UUID NOT NULL REFERENCES users(user_id),
        started_at TIMESTAMP DEFAULT NULL,
        completed_at TIMESTAMP DEFAULT NULL,
        percentage DECIMAL(5, 2),
        total_points INT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS attempt_answers (
        answer_attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        attempt_id UUID NOT NULL REFERENCES test_attempts(attempt_id),
        question_id UUID NOT NULL REFERENCES questions(question_id),
        -- Nullable: a row is recorded once the question is shown, before the student picks an option.
        selected_option_id UUID REFERENCES answer_options(option_id) DEFAULT NULL,
        points_awarded INT CHECK (points_awarded IN (30, -10, 0))
    );
    """,
    """
    CREATE OR REPLACE FUNCTION enforce_max_answer_options() RETURNS trigger AS $$
    BEGIN
        -- Lock the parent question so concurrent inserts can't both pass the count.
        PERFORM 1 FROM questions WHERE question_id = NEW.question_id FOR UPDATE;
        IF (
            SELECT COUNT(*) FROM answer_options
            WHERE question_id = NEW.question_id AND option_id <> NEW.option_id
        ) >= 4 THEN
            RAISE EXCEPTION 'A question can have at most 4 answer options';
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """,
    "DROP TRIGGER IF EXISTS answer_options_max_four ON answer_options;",
    """
    CREATE TRIGGER answer_options_max_four
    BEFORE INSERT OR UPDATE OF question_id ON answer_options
    FOR EACH ROW EXECUTE FUNCTION enforce_max_answer_options();
    
    # Add missing columns to existing databases
    "ALTER TABLE tests ADD COLUMN IF NOT EXISTS description TEXT NOT NULL DEFAULT '';",
    "ALTER TABLE tests ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;",
    "ALTER TABLE tests ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT FALSE;",
    "ALTER TABLE questions ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;",

    # Singleton row (company_info_id = 'main') holding the landing page's product
    # and contact info; TEXT key keeps the seed INSERT's ON CONFLICT target stable.
    """,
    """
    CREATE TABLE IF NOT EXISTS company_info (
        company_info_id TEXT PRIMARY KEY DEFAULT 'main',
        product_name VARCHAR(100) NOT NULL,
        product_description TEXT NOT NULL,
        contact_email VARCHAR(100) NOT NULL,
        contact_phone VARCHAR(30) NOT NULL,
        contact_address VARCHAR(255) NOT NULL
    );
    """,
    """
    INSERT INTO company_info (
        company_info_id, product_name, product_description, contact_email, contact_phone, contact_address
    )
    VALUES (
        'main',
        'Reinforcement Testing Platform',
        'An adaptive testing platform that helps students reinforce what they have learned through targeted practice tests.',
        'contact@bluesharklabs.app',
        '+44 1234 567890',
        'Blue Shark Labs, Weston-super-Mare, UK'
    )
    ON CONFLICT (company_info_id) DO NOTHING;
    """,
    # Indexes on foreign key columns (Postgres doesn't create these automatically).
    "CREATE INDEX IF NOT EXISTS idx_tests_subject_id ON tests(subject_id);",
    "CREATE INDEX IF NOT EXISTS idx_tests_created_by ON tests(created_by);",
    "CREATE INDEX IF NOT EXISTS idx_test_assignments_student_id ON test_assignments(student_id);",
    "CREATE INDEX IF NOT EXISTS idx_test_assignments_test_id ON test_assignments(test_id);",
    "CREATE INDEX IF NOT EXISTS idx_subject_lecturers_user_id ON subject_lecturers(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_questions_subject_id ON questions(subject_id);",
    "CREATE INDEX IF NOT EXISTS idx_answer_options_question_id ON answer_options(question_id);",
    "CREATE INDEX IF NOT EXISTS idx_test_attempts_test_id ON test_attempts(test_id);",
    "CREATE INDEX IF NOT EXISTS idx_test_attempts_user_id ON test_attempts(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempt_answers_attempt_id ON attempt_answers(attempt_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempt_answers_question_id ON attempt_answers(question_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempt_answers_selected_option_id ON attempt_answers(selected_option_id);",
]


def migrate():
    load_dotenv(ROOT_DIR / "dev.env")
    from database.connection import PostgresConnectionProvider

    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        for statement in SCHEMA_STATEMENTS:
            cur.execute(statement)
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
