"""Seed repeatable sample data for manually testing the student dashboard.

Attaches the data to the dev student created by `seed_dev_users`, so run
`make seed-dev-users` first, then
`python -m database.migrations.seed_student_dashboard` or
`make seed-student-dashboard`. Never run against prod.
"""

from database.connection import PostgresConnectionProvider
from database.migrations.seed_dev_users import DEV_USERS

DEV_STUDENT_EMAIL = next(email for _, _, email, _, role in DEV_USERS if role == "student")

SEED_STATEMENTS = [
    """
    INSERT INTO subjects (subject_id, name, description)
    VALUES
        (
            '00000000-0000-4000-8000-000000000010',
            'Mathematics',
            'Sample subject for student dashboard testing'
        ),
        (
            '00000000-0000-4000-8000-000000000011',
            'Computer Science',
            'Sample subject for student dashboard testing'
        )
    ON CONFLICT (subject_id) DO UPDATE SET
        name = EXCLUDED.name,
        description = EXCLUDED.description;
    """,
    """
    INSERT INTO tests (test_id, subject_id, title, question_count, time_limit_minutes)
    VALUES
        (
            '00000000-0000-4000-8000-000000000020',
            '00000000-0000-4000-8000-000000000010',
            'Algebra Practice',
            10,
            20
        ),
        (
            '00000000-0000-4000-8000-000000000021',
            '00000000-0000-4000-8000-000000000011',
            'Introduction to Computing',
            5,
            15
        ),
        (
            '00000000-0000-4000-8000-000000000022',
            '00000000-0000-4000-8000-000000000010',
            'Algebra Fundamentals',
            10,
            20
        ),
        (
            '00000000-0000-4000-8000-000000000023',
            '00000000-0000-4000-8000-000000000010',
            'Functions and Graphs',
            10,
            20
        ),
        (
            '00000000-0000-4000-8000-000000000024',
            '00000000-0000-4000-8000-000000000010',
            'Calculus Basics',
            10,
            20
        ),
        (
            '00000000-0000-4000-8000-000000000025',
            '00000000-0000-4000-8000-000000000010',
            'Statistics Practice',
            10,
            20
        ),
        (
            '00000000-0000-4000-8000-000000000026',
            '00000000-0000-4000-8000-000000000011',
            'Programming Fundamentals',
            5,
            15
        ),
        (
            '00000000-0000-4000-8000-000000000027',
            '00000000-0000-4000-8000-000000000011',
            'Data Structures',
            5,
            15
        ),
        (
            '00000000-0000-4000-8000-000000000028',
            '00000000-0000-4000-8000-000000000011',
            'Computer Systems',
            5,
            15
        ),
        (
            '00000000-0000-4000-8000-000000000029',
            '00000000-0000-4000-8000-000000000011',
            'Database Concepts',
            5,
            15
        )
    ON CONFLICT (test_id) DO UPDATE SET
        subject_id = EXCLUDED.subject_id,
        title = EXCLUDED.title,
        question_count = EXCLUDED.question_count,
        time_limit_minutes = EXCLUDED.time_limit_minutes;
    """,
    """
    INSERT INTO test_assignments (test_id, student_id, assigned_at)
    VALUES
        (
            '00000000-0000-4000-8000-000000000020',
            %(student_id)s,
            TIMESTAMP '2026-10-30 09:00:00'
        ),
        (
            '00000000-0000-4000-8000-000000000021',
            %(student_id)s,
            TIMESTAMP '2026-10-29 09:00:00'
        ),
        (
            '00000000-0000-4000-8000-000000000022',
            %(student_id)s,
            TIMESTAMP '2026-11-08 09:00:00'
        ),
        (
            '00000000-0000-4000-8000-000000000023',
            %(student_id)s,
            TIMESTAMP '2026-11-07 09:00:00'
        ),
        (
            '00000000-0000-4000-8000-000000000024',
            %(student_id)s,
            TIMESTAMP '2026-11-06 09:00:00'
        ),
        (
            '00000000-0000-4000-8000-000000000025',
            %(student_id)s,
            TIMESTAMP '2026-11-05 09:00:00'
        ),
        (
            '00000000-0000-4000-8000-000000000026',
            %(student_id)s,
            TIMESTAMP '2026-11-04 09:00:00'
        ),
        (
            '00000000-0000-4000-8000-000000000027',
            %(student_id)s,
            TIMESTAMP '2026-11-03 09:00:00'
        ),
        (
            '00000000-0000-4000-8000-000000000028',
            %(student_id)s,
            TIMESTAMP '2026-11-02 09:00:00'
        ),
        (
            '00000000-0000-4000-8000-000000000029',
            %(student_id)s,
            TIMESTAMP '2026-11-01 09:00:00'
        )
    ON CONFLICT (test_id, student_id) DO UPDATE SET
        assigned_at = EXCLUDED.assigned_at;
    """,
    """
    INSERT INTO questions (question_id, subject_id, question_text)
    VALUES
        (
            '00000000-0000-4000-8000-000000000040',
            '00000000-0000-4000-8000-000000000011',
            'Sample question 1'
        ),
        (
            '00000000-0000-4000-8000-000000000041',
            '00000000-0000-4000-8000-000000000011',
            'Sample question 2'
        ),
        (
            '00000000-0000-4000-8000-000000000042',
            '00000000-0000-4000-8000-000000000011',
            'Sample question 3'
        ),
        (
            '00000000-0000-4000-8000-000000000043',
            '00000000-0000-4000-8000-000000000011',
            'Sample question 4'
        ),
        (
            '00000000-0000-4000-8000-000000000044',
            '00000000-0000-4000-8000-000000000011',
            'Sample question 5'
        )
    ON CONFLICT (question_id) DO UPDATE SET
        subject_id = EXCLUDED.subject_id,
        question_text = EXCLUDED.question_text;
    """,
    """
    INSERT INTO answer_options (option_id, question_id, option_text, is_correct)
    VALUES
        ('00000000-0000-4000-8000-000000000070', '00000000-0000-4000-8000-000000000040', 'Correct answer', TRUE),
        ('00000000-0000-4000-8000-000000000071', '00000000-0000-4000-8000-000000000040', 'Incorrect answer', FALSE),
        ('00000000-0000-4000-8000-000000000072', '00000000-0000-4000-8000-000000000041', 'Correct answer', TRUE),
        ('00000000-0000-4000-8000-000000000073', '00000000-0000-4000-8000-000000000041', 'Incorrect answer', FALSE),
        ('00000000-0000-4000-8000-000000000074', '00000000-0000-4000-8000-000000000042', 'Correct answer', TRUE),
        ('00000000-0000-4000-8000-000000000075', '00000000-0000-4000-8000-000000000042', 'Incorrect answer', FALSE),
        ('00000000-0000-4000-8000-000000000076', '00000000-0000-4000-8000-000000000043', 'Correct answer', TRUE),
        ('00000000-0000-4000-8000-000000000077', '00000000-0000-4000-8000-000000000043', 'Incorrect answer', FALSE),
        ('00000000-0000-4000-8000-000000000078', '00000000-0000-4000-8000-000000000044', 'Correct answer', TRUE),
        ('00000000-0000-4000-8000-000000000079', '00000000-0000-4000-8000-000000000044', 'Incorrect answer', FALSE)
    ON CONFLICT (option_id) DO UPDATE SET
        question_id = EXCLUDED.question_id,
        option_text = EXCLUDED.option_text,
        is_correct = EXCLUDED.is_correct;
    """,
    """
    INSERT INTO test_attempts (
        attempt_id, test_id, user_id, started_at, completed_at, percentage, total_points
    )
    VALUES (
        '00000000-0000-4000-8000-000000000050',
        '00000000-0000-4000-8000-000000000021',
        %(student_id)s,
        TIMESTAMP '2026-10-31 14:00:00',
        TIMESTAMP '2026-10-31 14:30:00',
        80.00,
        110
    )
    ON CONFLICT (attempt_id) DO UPDATE SET
        test_id = EXCLUDED.test_id,
        user_id = EXCLUDED.user_id,
        started_at = EXCLUDED.started_at,
        completed_at = EXCLUDED.completed_at,
        percentage = EXCLUDED.percentage,
        total_points = EXCLUDED.total_points;
    """,
    """
    INSERT INTO test_attempts (
        attempt_id, test_id, user_id, started_at, completed_at, percentage, total_points
    )
    VALUES
        (
            '00000000-0000-4000-8000-000000000051',
            '00000000-0000-4000-8000-000000000026',
            %(student_id)s,
            TIMESTAMP '2026-11-04 10:00:00',
            TIMESTAMP '2026-11-04 10:25:00',
            100.00,
            150
        ),
        (
            '00000000-0000-4000-8000-000000000052',
            '00000000-0000-4000-8000-000000000027',
            %(student_id)s,
            TIMESTAMP '2026-11-03 10:00:00',
            TIMESTAMP '2026-11-03 10:25:00',
            80.00,
            110
        ),
        (
            '00000000-0000-4000-8000-000000000053',
            '00000000-0000-4000-8000-000000000028',
            %(student_id)s,
            TIMESTAMP '2026-11-02 10:00:00',
            TIMESTAMP '2026-11-02 10:25:00',
            60.00,
            70
        ),
        (
            '00000000-0000-4000-8000-000000000054',
            '00000000-0000-4000-8000-000000000029',
            %(student_id)s,
            TIMESTAMP '2026-11-01 10:00:00',
            TIMESTAMP '2026-11-01 10:25:00',
            40.00,
            30
        )
    ON CONFLICT (attempt_id) DO UPDATE SET
        test_id = EXCLUDED.test_id,
        user_id = EXCLUDED.user_id,
        started_at = EXCLUDED.started_at,
        completed_at = EXCLUDED.completed_at,
        percentage = EXCLUDED.percentage,
        total_points = EXCLUDED.total_points;
    """,
    """
    INSERT INTO attempt_answers (
        answer_attempt_id, attempt_id, question_id, selected_option_id, points_awarded
    )
    VALUES
        (
            '00000000-0000-4000-8000-000000000060',
            '00000000-0000-4000-8000-000000000050',
            '00000000-0000-4000-8000-000000000040',
            '00000000-0000-4000-8000-000000000070',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000061',
            '00000000-0000-4000-8000-000000000050',
            '00000000-0000-4000-8000-000000000041',
            '00000000-0000-4000-8000-000000000072',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000062',
            '00000000-0000-4000-8000-000000000050',
            '00000000-0000-4000-8000-000000000042',
            '00000000-0000-4000-8000-000000000074',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000063',
            '00000000-0000-4000-8000-000000000050',
            '00000000-0000-4000-8000-000000000043',
            '00000000-0000-4000-8000-000000000076',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000064',
            '00000000-0000-4000-8000-000000000050',
            '00000000-0000-4000-8000-000000000044',
            '00000000-0000-4000-8000-000000000079',
            -10
        ),
        (
            '00000000-0000-4000-8000-000000000065',
            '00000000-0000-4000-8000-000000000051',
            '00000000-0000-4000-8000-000000000040',
            '00000000-0000-4000-8000-000000000070',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000066',
            '00000000-0000-4000-8000-000000000051',
            '00000000-0000-4000-8000-000000000041',
            '00000000-0000-4000-8000-000000000072',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000067',
            '00000000-0000-4000-8000-000000000051',
            '00000000-0000-4000-8000-000000000042',
            '00000000-0000-4000-8000-000000000074',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000068',
            '00000000-0000-4000-8000-000000000051',
            '00000000-0000-4000-8000-000000000043',
            '00000000-0000-4000-8000-000000000076',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000069',
            '00000000-0000-4000-8000-000000000051',
            '00000000-0000-4000-8000-000000000044',
            '00000000-0000-4000-8000-000000000078',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000070',
            '00000000-0000-4000-8000-000000000052',
            '00000000-0000-4000-8000-000000000040',
            '00000000-0000-4000-8000-000000000070',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000071',
            '00000000-0000-4000-8000-000000000052',
            '00000000-0000-4000-8000-000000000041',
            '00000000-0000-4000-8000-000000000072',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000072',
            '00000000-0000-4000-8000-000000000052',
            '00000000-0000-4000-8000-000000000042',
            '00000000-0000-4000-8000-000000000074',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000073',
            '00000000-0000-4000-8000-000000000052',
            '00000000-0000-4000-8000-000000000043',
            '00000000-0000-4000-8000-000000000077',
            -10
        ),
        (
            '00000000-0000-4000-8000-000000000074',
            '00000000-0000-4000-8000-000000000052',
            '00000000-0000-4000-8000-000000000044',
            '00000000-0000-4000-8000-000000000079',
            -10
        ),
        (
            '00000000-0000-4000-8000-000000000075',
            '00000000-0000-4000-8000-000000000053',
            '00000000-0000-4000-8000-000000000040',
            '00000000-0000-4000-8000-000000000070',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000076',
            '00000000-0000-4000-8000-000000000053',
            '00000000-0000-4000-8000-000000000041',
            '00000000-0000-4000-8000-000000000072',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000077',
            '00000000-0000-4000-8000-000000000053',
            '00000000-0000-4000-8000-000000000042',
            '00000000-0000-4000-8000-000000000074',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000078',
            '00000000-0000-4000-8000-000000000053',
            '00000000-0000-4000-8000-000000000043',
            '00000000-0000-4000-8000-000000000077',
            -10
        ),
        (
            '00000000-0000-4000-8000-000000000079',
            '00000000-0000-4000-8000-000000000053',
            '00000000-0000-4000-8000-000000000044',
            '00000000-0000-4000-8000-000000000079',
            -10
        ),
        (
            '00000000-0000-4000-8000-000000000080',
            '00000000-0000-4000-8000-000000000054',
            '00000000-0000-4000-8000-000000000040',
            '00000000-0000-4000-8000-000000000070',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000081',
            '00000000-0000-4000-8000-000000000054',
            '00000000-0000-4000-8000-000000000041',
            '00000000-0000-4000-8000-000000000072',
            30
        ),
        (
            '00000000-0000-4000-8000-000000000082',
            '00000000-0000-4000-8000-000000000054',
            '00000000-0000-4000-8000-000000000042',
            '00000000-0000-4000-8000-000000000075',
            -10
        ),
        (
            '00000000-0000-4000-8000-000000000083',
            '00000000-0000-4000-8000-000000000054',
            '00000000-0000-4000-8000-000000000043',
            '00000000-0000-4000-8000-000000000077',
            -10
        ),
        (
            '00000000-0000-4000-8000-000000000084',
            '00000000-0000-4000-8000-000000000054',
            '00000000-0000-4000-8000-000000000044',
            '00000000-0000-4000-8000-000000000079',
            -10
        )
    ON CONFLICT (answer_attempt_id) DO UPDATE SET
        attempt_id = EXCLUDED.attempt_id,
        question_id = EXCLUDED.question_id,
        selected_option_id = EXCLUDED.selected_option_id,
        points_awarded = EXCLUDED.points_awarded;
    """,
]

ALGEBRA_TEST_ID = "00000000-0000-4000-8000-000000000020"
COMPUTING_TEST_ID = "00000000-0000-4000-8000-000000000021"

# (user_id, first_name, last_name, student_number)
LEADERBOARD_STUDENTS = [
    ("00000000-0000-4000-8000-000000000002", "Priya", "Patel", "DEMO-002"),
    ("00000000-0000-4000-8000-000000000003", "Tom", "Baker", "DEMO-003"),
    ("00000000-0000-4000-8000-000000000004", "Aisha", "Khan", "DEMO-004"),
    ("00000000-0000-4000-8000-000000000005", "Grace", "Okafor", "DEMO-005"),
    ("00000000-0000-4000-8000-000000000006", "Owen", "Hughes", "DEMO-006"),
    ("00000000-0000-4000-8000-000000000007", "Ben", "Carter", "DEMO-007"),
]

# (attempt_id, test_id, user_id, completed_at, percentage, total_points)
# Points follow +30 correct / -10 incorrect. Tom ties Michael in Computing to
# exercise tie-breaking, Grace has two Algebra attempts to exercise aggregation,
# and six Computing entrants exercise the top-five limit.
LEADERBOARD_ATTEMPTS = [
    ("00000000-0000-4000-8000-000000000080", ALGEBRA_TEST_ID, "00000000-0000-4000-8000-000000000002", "2026-11-01 10:20:00", 80.00, 220),
    ("00000000-0000-4000-8000-000000000081", ALGEBRA_TEST_ID, "00000000-0000-4000-8000-000000000003", "2026-11-01 11:15:00", 90.00, 260),
    ("00000000-0000-4000-8000-000000000082", ALGEBRA_TEST_ID, "00000000-0000-4000-8000-000000000004", "2026-11-02 09:40:00", 100.00, 300),
    ("00000000-0000-4000-8000-000000000083", ALGEBRA_TEST_ID, "00000000-0000-4000-8000-000000000005", "2026-11-02 13:10:00", 70.00, 180),
    ("00000000-0000-4000-8000-000000000084", ALGEBRA_TEST_ID, "00000000-0000-4000-8000-000000000005", "2026-11-05 13:10:00", 80.00, 220),
    ("00000000-0000-4000-8000-000000000085", ALGEBRA_TEST_ID, "00000000-0000-4000-8000-000000000006", "2026-11-03 15:00:00", 60.00, 140),
    ("00000000-0000-4000-8000-000000000086", ALGEBRA_TEST_ID, "00000000-0000-4000-8000-000000000007", "2026-11-03 16:30:00", 50.00, 100),
    ("00000000-0000-4000-8000-000000000087", COMPUTING_TEST_ID, "00000000-0000-4000-8000-000000000002", "2026-11-01 14:25:00", 100.00, 150),
    ("00000000-0000-4000-8000-000000000088", COMPUTING_TEST_ID, "00000000-0000-4000-8000-000000000003", "2026-11-02 10:05:00", 80.00, 110),
    ("00000000-0000-4000-8000-000000000089", COMPUTING_TEST_ID, "00000000-0000-4000-8000-000000000004", "2026-11-02 11:45:00", 60.00, 70),
    ("00000000-0000-4000-8000-000000000090", COMPUTING_TEST_ID, "00000000-0000-4000-8000-000000000005", "2026-11-03 09:30:00", 40.00, 30),
    ("00000000-0000-4000-8000-000000000091", COMPUTING_TEST_ID, "00000000-0000-4000-8000-000000000006", "2026-11-04 12:00:00", 20.00, -10),
]


def _seed_leaderboard_data(cur):
    for user_id, first_name, last_name, student_number in LEADERBOARD_STUDENTS:
        cur.execute(
            """
            INSERT INTO users (user_id, first_name, last_name, email, password_hash, role)
            VALUES (%s, %s, %s, %s, 'seed-data-only', 'student')
            ON CONFLICT (user_id) DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                email = EXCLUDED.email,
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role;
            """,
            (user_id, first_name, last_name, f"{first_name}.{last_name}@example.test".lower()),
        )
        cur.execute(
            """
            INSERT INTO students (user_id, student_number, course_title, is_approved)
            VALUES (%s, %s, 'BSc Computing', TRUE)
            ON CONFLICT (user_id) DO UPDATE SET
                student_number = EXCLUDED.student_number,
                course_title = EXCLUDED.course_title,
                is_approved = EXCLUDED.is_approved;
            """,
            (user_id, student_number),
        )

    for attempt_id, test_id, user_id, completed_at, percentage, total_points in LEADERBOARD_ATTEMPTS:
        cur.execute(
            """
            INSERT INTO test_assignments (test_id, student_id, assigned_at)
            VALUES (%s, %s, TIMESTAMP '2026-10-29 09:00:00')
            ON CONFLICT (test_id, student_id) DO NOTHING;
            """,
            (test_id, user_id),
        )
        cur.execute(
            """
            INSERT INTO test_attempts (
                attempt_id, test_id, user_id, started_at, completed_at, percentage, total_points
            )
            VALUES (
                %s, %s, %s,
                %s::timestamp - INTERVAL '20 minutes', %s::timestamp, %s, %s
            )
            ON CONFLICT (attempt_id) DO UPDATE SET
                test_id = EXCLUDED.test_id,
                user_id = EXCLUDED.user_id,
                started_at = EXCLUDED.started_at,
                completed_at = EXCLUDED.completed_at,
                percentage = EXCLUDED.percentage,
                total_points = EXCLUDED.total_points;
            """,
            (attempt_id, test_id, user_id, completed_at, completed_at, percentage, total_points),
        )


def seed_student_dashboard():
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        cur.execute(
            """
            SELECT u.user_id
            FROM users AS u
            JOIN students AS s ON s.user_id = u.user_id
            WHERE u.email = %s AND u.role = 'student';
            """,
            (DEV_STUDENT_EMAIL,),
        )
        row = cur.fetchone()
        if row is None:
            raise RuntimeError(
                f"Dev student {DEV_STUDENT_EMAIL} not found. Run `make seed-dev-users` first."
            )
        params = {"student_id": row[0]}
        for statement in SEED_STATEMENTS:
            cur.execute(statement, params)
    print(f"Student dashboard sample data seeded for {DEV_STUDENT_EMAIL}.")


if __name__ == "__main__":
    seed_student_dashboard()
