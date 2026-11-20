import re

from database.migrations.seed_student_dashboard import SEED_STATEMENTS


def test_seeded_math_test_has_a_varied_four_option_question_pool():
    math_subject_id = "00000000-0000-4000-8000-000000000010"
    question_statement = next(
        statement for statement in SEED_STATEMENTS if "INSERT INTO questions" in statement
    )
    option_statement = next(
        statement for statement in SEED_STATEMENTS if "INSERT INTO answer_options" in statement
    )

    math_question_ids = set(
        re.findall(
            rf"\(\s*'([^']+)',\s*'{math_subject_id}',\s*'[^']+'\s*\)",
            question_statement,
        )
    )
    options_by_question = {}
    for _, question_id, is_correct in re.findall(
        r"\('([^']+)', '([^']+)', '[^']*', (TRUE|FALSE)\)",
        option_statement,
    ):
        options_by_question.setdefault(question_id, []).append(is_correct == "TRUE")

    assert len(math_question_ids) > 10
    for question_id in math_question_ids:
        question_options = options_by_question[question_id]
        assert len(question_options) == 4
        assert sum(question_options) == 1
