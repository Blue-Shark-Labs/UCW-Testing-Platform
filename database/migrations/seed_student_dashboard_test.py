from database.migrations.seed_data import load_seed_data
from database.migrations.seed_student_dashboard import build_activity_plan, build_attempt

MATH_SUBJECT = "mathematics"


def _plan():
    return build_activity_plan(
        load_seed_data("tests")["tests"],
        load_seed_data("questions")["questions"],
        load_seed_data("test_activity"),
    )


def test_seeded_math_test_has_a_varied_four_option_question_pool():
    questions = load_seed_data("questions")["questions"]
    math_questions = [q for q in questions if q["subject"] == MATH_SUBJECT]

    assert len(math_questions) > 10
    for question in math_questions:
        assert len(question["options"]) == 4
        assert sum(option["isCorrect"] for option in question["options"]) == 1


def test_every_question_has_one_correct_and_an_incorrect_option():
    for question in load_seed_data("questions")["questions"]:
        flags = [option["isCorrect"] for option in question["options"]]
        assert flags.count(True) == 1
        assert False in flags


def test_subject_lecturers_are_seeded_staff():
    staff = {
        user["email"]
        for user in load_seed_data("users")["users"]
        if user["role"] in ("lecturer", "admin")
    }
    for subject in load_seed_data("subjects")["subjects"]:
        assert set(subject.get("lecturerEmails", [])) <= staff, subject["key"]


def test_activity_only_references_seeded_students():
    students = {
        user["email"]
        for user in load_seed_data("users")["users"]
        if user["role"] == "student"
    }
    activity_emails = [s["email"] for s in load_seed_data("test_activity")["students"]]

    assert len(activity_emails) == len(set(activity_emails))
    assert set(activity_emails) <= students


def test_plan_simulates_many_students_with_different_completed_tests():
    plan = _plan()
    completed_sets = {
        frozenset(attempt["test_id"] for attempt in student["attempts"]) for student in plan
    }
    attempt_ids = [a["attempt_id"] for s in plan for a in s["attempts"]]

    assert len(plan) >= 15
    assert len(completed_sets) >= 10
    assert len(attempt_ids) == len(set(attempt_ids))
    for student in plan:
        for attempt in student["attempts"]:
            assert attempt["test_id"] in student["assigned_test_ids"]


def test_build_attempt_scores_from_correct_count():
    test = {"key": "t", "testId": "test-1", "questionCount": 5}
    pool = [
        {
            "questionId": f"q{i}",
            "options": [
                {"optionId": f"q{i}-right", "isCorrect": True},
                {"optionId": f"q{i}-wrong", "isCorrect": False},
            ],
        }
        for i in range(6)
    ]
    completed = {"test": "t", "correct": 3, "completedAt": "2026-11-01T10:00:00", "durationMinutes": 7}

    attempt = build_attempt("a@example.test", test, completed, pool, 12)

    assert attempt["percentage"] == 60.0
    assert attempt["total_points"] == 70
    assert (attempt["completed_at"] - attempt["started_at"]).total_seconds() == 7 * 60
    assert len(attempt["answers"]) == 5
    assert len({a["question_id"] for a in attempt["answers"]}) == 5
    assert [a["points_awarded"] for a in attempt["answers"]].count(30) == 3
    for answer in attempt["answers"]:
        expected = "right" if answer["points_awarded"] == 30 else "wrong"
        assert answer["selected_option_id"].endswith(expected)
    assert build_attempt("a@example.test", test, completed, pool, 12) == attempt
