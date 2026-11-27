"""Seed repeatable sample subjects, tests, questions and student test activity.

Reads the JSON files in `database/migrations/seed_data/` and attaches activity
to the students created by `seed_dev_users`, so run `make seed-dev-users`
first, then `make seed-student-dashboard`. Never run against prod.
"""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta

from database.connection import PostgresConnectionProvider
from database.migrations.seed_data import load_seed_data

SEED_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "ucw-testing-platform:seed")
CORRECT_POINTS = 30
INCORRECT_POINTS = -10


def build_attempt(email, test, completed, question_pool, default_duration_minutes):
    """Derive a completed attempt and its answers from a `correct` answer count."""
    question_count = test["questionCount"]
    correct = completed["correct"]
    if not 0 <= correct <= question_count:
        raise ValueError(f"{email}: correct must be 0-{question_count} for {test['key']}.")
    if len(question_pool) < question_count:
        raise ValueError(f"Not enough questions in the pool for {test['key']}.")

    completed_at = datetime.fromisoformat(completed["completedAt"])
    duration = completed.get("durationMinutes", default_duration_minutes)
    attempt_id = uuid.uuid5(
        SEED_NAMESPACE, f"attempt:{email}:{test['key']}:{completed['completedAt']}"
    )
    # Rotate the pool per attempt so students miss different questions.
    offset = attempt_id.int % len(question_pool)
    questions = (question_pool[offset:] + question_pool[:offset])[:question_count]

    answers = []
    for index, question in enumerate(questions):
        is_correct = index < correct
        option = next(o for o in question["options"] if o["isCorrect"] == is_correct)
        answers.append({
            "answer_attempt_id": uuid.uuid5(
                SEED_NAMESPACE, f"answer:{attempt_id}:{question['questionId']}"
            ),
            "question_id": question["questionId"],
            "selected_option_id": option["optionId"],
            "points_awarded": CORRECT_POINTS if is_correct else INCORRECT_POINTS,
        })

    return {
        "attempt_id": attempt_id,
        "test_id": test["testId"],
        "started_at": completed_at - timedelta(minutes=duration),
        "completed_at": completed_at,
        "percentage": round(correct * 100 / question_count, 2),
        "total_points": correct * CORRECT_POINTS + (question_count - correct) * INCORRECT_POINTS,
        "answers": answers,
    }


def build_activity_plan(tests, questions, activity):
    """Resolve test_activity.json into per-student assignments and attempts."""
    tests_by_key = {test["key"]: test for test in tests}
    pools = defaultdict(list)
    for question in questions:
        pools[question["subject"]].append(question)

    plan = []
    for student in activity["students"]:
        email = student["email"]
        assigned_keys = (
            list(tests_by_key)
            if student["assignedTests"] == "all"
            else student["assignedTests"]
        )
        unknown = set(assigned_keys) - set(tests_by_key)
        if unknown:
            raise ValueError(f"{email}: unknown tests {sorted(unknown)}.")

        attempts = []
        for completed in student["completedTests"]:
            if completed["test"] not in assigned_keys:
                raise ValueError(f"{email}: {completed['test']} is completed but not assigned.")
            test = tests_by_key[completed["test"]]
            attempts.append(build_attempt(
                email,
                test,
                completed,
                pools[test["subject"]],
                activity["defaultDurationMinutes"],
            ))

        plan.append({
            "email": email,
            "assigned_test_ids": [tests_by_key[key]["testId"] for key in assigned_keys],
            "attempts": attempts,
        })
    return plan


def _seed_catalogue(cur, subjects, tests, questions):
    subject_ids = {subject["key"]: subject["subjectId"] for subject in subjects}
    cur.executemany(
        """
        INSERT INTO subjects (subject_id, name, description, is_active)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (subject_id) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            is_active = EXCLUDED.is_active;
        """,
        [(s["subjectId"], s["name"], s["description"], s.get("isActive", True)) for s in subjects],
    )
    cur.executemany(
        """
        INSERT INTO subject_lecturers (subject_id, user_id)
        SELECT %s, user_id FROM users WHERE email = %s AND role IN ('lecturer', 'admin')
        ON CONFLICT (subject_id, user_id) DO NOTHING;
        """,
        [(s["subjectId"], email) for s in subjects for email in s.get("lecturerEmails", [])],
    )
    cur.executemany(
        """
        INSERT INTO tests (
            test_id, subject_id, title, description, question_count, time_limit_minutes
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (test_id) DO UPDATE SET
            subject_id = EXCLUDED.subject_id,
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            question_count = EXCLUDED.question_count,
            time_limit_minutes = EXCLUDED.time_limit_minutes;
        """,
        [
            (
                t["testId"],
                subject_ids[t["subject"]],
                t["title"],
                t.get("description", ""),
                t["questionCount"],
                t["timeLimitMinutes"],
            )
            for t in tests
        ],
    )
    cur.executemany(
        """
        INSERT INTO questions (question_id, subject_id, question_text)
        VALUES (%s, %s, %s)
        ON CONFLICT (question_id) DO UPDATE SET
            subject_id = EXCLUDED.subject_id,
            question_text = EXCLUDED.question_text;
        """,
        [(q["questionId"], subject_ids[q["subject"]], q["text"]) for q in questions],
    )
    cur.executemany(
        """
        INSERT INTO answer_options (option_id, question_id, option_text, is_correct)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (option_id) DO UPDATE SET
            question_id = EXCLUDED.question_id,
            option_text = EXCLUDED.option_text,
            is_correct = EXCLUDED.is_correct;
        """,
        [
            (o["optionId"], q["questionId"], o["text"], o["isCorrect"])
            for q in questions
            for o in q["options"]
        ],
    )


def _seed_student_activity(cur, student, assigned_at):
    cur.execute(
        """
        SELECT u.user_id
        FROM users AS u
        JOIN students AS s ON s.user_id = u.user_id
        WHERE u.email = %s AND u.role = 'student';
        """,
        (student["email"],),
    )
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(
            f"Student {student['email']} not found. Run `make seed-dev-users` first."
        )
    student_id = row[0]

    cur.executemany(
        """
        INSERT INTO test_assignments (test_id, student_id, assigned_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (test_id, student_id) DO NOTHING;
        """,
        [(test_id, student_id, assigned_at) for test_id in student["assigned_test_ids"]],
    )
    for attempt in student["attempts"]:
        cur.execute(
            """
            INSERT INTO test_attempts (
                attempt_id, test_id, user_id, started_at, completed_at, percentage, total_points
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (attempt_id) DO UPDATE SET
                test_id = EXCLUDED.test_id,
                user_id = EXCLUDED.user_id,
                started_at = EXCLUDED.started_at,
                completed_at = EXCLUDED.completed_at,
                percentage = EXCLUDED.percentage,
                total_points = EXCLUDED.total_points;
            """,
            (
                attempt["attempt_id"],
                attempt["test_id"],
                student_id,
                attempt["started_at"],
                attempt["completed_at"],
                attempt["percentage"],
                attempt["total_points"],
            ),
        )
        cur.executemany(
            """
            INSERT INTO attempt_answers (
                answer_attempt_id, attempt_id, question_id, selected_option_id, points_awarded
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (answer_attempt_id) DO UPDATE SET
                attempt_id = EXCLUDED.attempt_id,
                question_id = EXCLUDED.question_id,
                selected_option_id = EXCLUDED.selected_option_id,
                points_awarded = EXCLUDED.points_awarded;
            """,
            [
                (
                    answer["answer_attempt_id"],
                    attempt["attempt_id"],
                    answer["question_id"],
                    answer["selected_option_id"],
                    answer["points_awarded"],
                )
                for answer in attempt["answers"]
            ],
        )


def seed_student_dashboard():
    subjects = load_seed_data("subjects")["subjects"]
    tests = load_seed_data("tests")["tests"]
    questions = load_seed_data("questions")["questions"]
    activity = load_seed_data("test_activity")
    plan = build_activity_plan(tests, questions, activity)
    assigned_at = datetime.fromisoformat(activity["defaultAssignedAt"])

    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        _seed_catalogue(cur, subjects, tests, questions)
        for student in plan:
            _seed_student_activity(cur, student, assigned_at)

    attempt_count = sum(len(student["attempts"]) for student in plan)
    print(f"Seeded test activity for {len(plan)} students ({attempt_count} completed attempts).")


if __name__ == "__main__":
    seed_student_dashboard()
