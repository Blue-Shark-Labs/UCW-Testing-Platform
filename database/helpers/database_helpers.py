# Database helper functions for interacting with the PostgreSQL database.

from domain.entities.company_info import CompanyInfo
from database.connection import PostgresConnectionProvider
from domain.entities.user import User


def row_to_company_info(row):
    """Maps a company_info table row to a CompanyInfo domain entity."""
    product_name, product_description, contact_email, contact_phone, contact_address = row
    return CompanyInfo(
        product_name=product_name,
        product_description=product_description,
        contact_email=contact_email,
        contact_phone=contact_phone,
        contact_address=contact_address,
    )

def get_assigned_tests(student_id):
	"""Return tests a student has not completed."""
	fields = ("test_id", "test_name", "subject_name", "question_count")
	query = """
		SELECT t.test_id, t.title, s.name, t.question_count
		FROM tests AS t
		JOIN subjects AS s ON s.subject_id = t.subject_id
		JOIN test_assignments AS assignment
		  ON assignment.test_id = t.test_id
		 AND assignment.student_id = %s
		WHERE NOT EXISTS (
			  SELECT 1
			  FROM test_attempts AS attempt
			  WHERE attempt.test_id = t.test_id
				AND attempt.user_id = %s
				AND attempt.completed_at IS NOT NULL
		  )
		ORDER BY t.title
	"""
	return _fetch_rows(query, (student_id, student_id), fields)


def get_completed_tests(student_id):
	"""Return completed attempts with their result summary for a student."""
	fields = (
		"attempt_id",
		"test_name",
		"completed_at",
		"question_count",
		"percentage",
		"total_points",
	)
	query = """
		SELECT attempt.attempt_id, t.title, attempt.completed_at,
			   COUNT(DISTINCT answer.question_id), attempt.percentage,
			   attempt.total_points
		FROM test_attempts AS attempt
		JOIN tests AS t ON t.test_id = attempt.test_id
		LEFT JOIN attempt_answers AS answer ON answer.attempt_id = attempt.attempt_id
		WHERE attempt.user_id = %s
		  AND attempt.completed_at IS NOT NULL
		GROUP BY attempt.attempt_id, t.title
		ORDER BY attempt.completed_at DESC
	"""
	return _fetch_rows(query, (student_id,), fields)


def start_or_resume_test_attempt(test_id, student_id):
	"""Start or resume an assigned test with a personalized question set."""
	with PostgresConnectionProvider().cursor() as cursor:
		cursor.execute(
			"""
			SELECT t.test_id, t.title, s.name, t.subject_id,
			       t.question_count, t.time_limit_minutes
			FROM tests AS t
			JOIN subjects AS s ON s.subject_id = t.subject_id
			JOIN test_assignments AS assignment
			  ON assignment.test_id = t.test_id
			 AND assignment.student_id = %s
			WHERE t.test_id = %s
			  AND NOT EXISTS (
				  SELECT 1 FROM test_attempts AS completed
				  WHERE completed.test_id = t.test_id
				    AND completed.user_id = %s
				    AND completed.completed_at IS NOT NULL
			  )
			FOR UPDATE OF assignment
			""",
			(student_id, test_id, student_id),
		)
		test = cursor.fetchone()
		if test is None:
			return None

		test_id, test_name, subject_name, subject_id, question_count, time_limit = test
		cursor.execute(
			"""
			SELECT attempt_id
			FROM test_attempts
			WHERE test_id = %s AND user_id = %s AND completed_at IS NULL
			ORDER BY started_at DESC
			LIMIT 1
			""",
			(test_id, student_id),
		)
		active_attempt = cursor.fetchone()

		if active_attempt is None:
			cursor.execute(
				"""
				SELECT q.question_id, q.question_text
				FROM questions AS q
				LEFT JOIN attempt_answers AS previous_answer
				  ON previous_answer.question_id = q.question_id
				LEFT JOIN test_attempts AS previous_attempt
				  ON previous_attempt.attempt_id = previous_answer.attempt_id
				 AND previous_attempt.user_id = %s
				 AND previous_attempt.completed_at IS NOT NULL
				WHERE q.subject_id = %s
				  AND EXISTS (
					  SELECT 1
					  FROM (
					      SELECT is_correct
					      FROM answer_options
					      WHERE question_id = q.question_id
					      ORDER BY option_id
					      LIMIT 4
					  ) AS available_option
					  WHERE available_option.is_correct
				  )
				GROUP BY q.question_id, q.question_text
				ORDER BY COUNT(previous_answer.answer_attempt_id)
				         FILTER (
				             WHERE previous_attempt.attempt_id IS NOT NULL
				               AND previous_answer.points_awarded = -10
				         ) DESC,
				         random()
				LIMIT %s
				""",
				(student_id, subject_id, question_count),
			)
			questions = cursor.fetchall()
			if not questions:
				return None

			cursor.execute(
				"""
				INSERT INTO test_attempts (test_id, user_id, started_at)
				VALUES (%s, %s, CURRENT_TIMESTAMP)
				RETURNING attempt_id
				""",
				(test_id, student_id),
			)
			attempt_id = cursor.fetchone()[0]
			for question_id, _ in questions:
				cursor.execute(
					"""
					INSERT INTO attempt_answers
						(attempt_id, question_id)
					VALUES (%s, %s)
					""",
					(attempt_id, question_id),
				)
		else:
			attempt_id = active_attempt[0]

		cursor.execute(
			"""
			SELECT q.question_id, q.question_text, answer.selected_option_id
			FROM attempt_answers AS answer
			JOIN questions AS q ON q.question_id = answer.question_id
			WHERE answer.attempt_id = %s
			ORDER BY answer.answer_attempt_id
			""",
			(attempt_id,),
		)
		questions = cursor.fetchall()
		if not questions:
			return None

		test_questions = []
		for question_id, question_text, selected_option_id in questions:
			cursor.execute(
				"""
				SELECT option_id, option_text
				FROM (
				    SELECT option_id, option_text
				    FROM answer_options
				    WHERE question_id = %s
				    ORDER BY option_id
				    LIMIT 4
				) AS available_options
				ORDER BY random()
				""",
				(question_id,),
			)
			options = [
				{"option_id": option_id, "option_text": option_text}
				for option_id, option_text in cursor.fetchall()
			]
			test_questions.append(
				{
					"question_id": question_id,
					"question_text": question_text,
					"selected_option_id": selected_option_id,
					"options": options,
				}
			)

		cursor.execute(
			"""
			SELECT CASE
			    WHEN t.time_limit_minutes IS NULL THEN NULL
			    ELSE GREATEST(
			        0,
			        FLOOR(EXTRACT(EPOCH FROM (
			            attempt.started_at
			            + t.time_limit_minutes * INTERVAL '1 minute'
			            - CURRENT_TIMESTAMP
			        )))::INTEGER
			    )
			END
			FROM test_attempts AS attempt
			JOIN tests AS t ON t.test_id = attempt.test_id
			WHERE attempt.attempt_id = %s
			""",
			(attempt_id,),
		)
		seconds_remaining = cursor.fetchone()[0]

		return {
			"attempt_id": attempt_id,
			"test_id": test_id,
			"test_name": test_name,
			"subject_name": subject_name,
			"time_limit_minutes": time_limit,
			"seconds_remaining": seconds_remaining,
			"questions": test_questions,
		}


def save_test_answer(test_id, attempt_id, student_id, question_id, option_id):
	"""Persist an answer only while its student's timed attempt remains open."""
	with PostgresConnectionProvider().cursor() as cursor:
		cursor.execute(
			"""
			UPDATE attempt_answers AS answer
			SET selected_option_id = %s
			FROM test_attempts AS attempt
			JOIN tests AS t ON t.test_id = attempt.test_id
			WHERE answer.attempt_id = attempt.attempt_id
			  AND answer.question_id = %s
			  AND attempt.attempt_id = %s
			  AND attempt.test_id = %s
			  AND attempt.user_id = %s
			  AND attempt.completed_at IS NULL
			  AND (
			      t.time_limit_minutes IS NULL
			      OR CURRENT_TIMESTAMP < attempt.started_at
			         + t.time_limit_minutes * INTERVAL '1 minute'
			  )
			  AND EXISTS (
			      SELECT 1
			      FROM (
			          SELECT option_id
			          FROM answer_options
			          WHERE question_id = answer.question_id
			          ORDER BY option_id
			          LIMIT 4
			      ) AS available_option
			      WHERE available_option.option_id = %s
			  )
			RETURNING answer.answer_attempt_id
			""",
			(option_id, question_id, attempt_id, test_id, student_id, option_id),
		)
		return cursor.fetchone() is not None


def submit_test_attempt(test_id, attempt_id, student_id, answers=None):
	"""Score and complete an attempt, recording unanswered questions as zero."""
	answers = answers or {}
	with PostgresConnectionProvider().cursor() as cursor:
		cursor.execute(
			"""
			SELECT t.time_limit_minutes,
			       t.title,
			       (
			           t.time_limit_minutes IS NOT NULL
			           AND CURRENT_TIMESTAMP >= attempt.started_at
			               + t.time_limit_minutes * INTERVAL '1 minute'
			       ) AS expired
			FROM test_attempts AS attempt
			JOIN tests AS t ON t.test_id = attempt.test_id
			WHERE attempt.attempt_id = %s
			  AND attempt.test_id = %s
			  AND attempt.user_id = %s
			  AND attempt.completed_at IS NULL
			FOR UPDATE OF attempt
			""",
			(attempt_id, test_id, student_id),
		)
		attempt = cursor.fetchone()
		if attempt is None:
			return None
		_, test_name, expired = attempt
		answers = {str(question_id): option_id for question_id, option_id in answers.items()}

		cursor.execute(
			"""
			SELECT question_id, selected_option_id
			FROM attempt_answers
			WHERE attempt_id = %s
			""",
			(attempt_id,),
		)
		attempt_questions = cursor.fetchall()
		correct_count = 0
		total_points = 0
		for question_id, saved_option_id in attempt_questions:
			selected_option_id = saved_option_id
			if not expired and str(question_id) in answers:
				selected_option_id = answers[str(question_id)]

			points_awarded = 0
			if selected_option_id is not None:
				cursor.execute(
					"""
					SELECT is_correct
					FROM (
					    SELECT option_id, is_correct
					    FROM answer_options
					    WHERE question_id = %s
					    ORDER BY option_id
					    LIMIT 4
					) AS available_option
					WHERE available_option.option_id = %s
					""",
					(question_id, selected_option_id),
				)
				option = cursor.fetchone()
				if option is None:
					raise ValueError("Selected answer does not belong to its question.")
				if option[0]:
					points_awarded = 30
					correct_count += 1
				else:
					points_awarded = -10
			total_points += points_awarded
			cursor.execute(
				"""
				UPDATE attempt_answers
				SET selected_option_id = %s, points_awarded = %s
				WHERE attempt_id = %s AND question_id = %s
				""",
				(selected_option_id, points_awarded, attempt_id, question_id),
			)

		question_count = len(attempt_questions)
		percentage = correct_count * 100.0 / question_count
		cursor.execute(
			"""
			UPDATE test_attempts
			SET completed_at = CURRENT_TIMESTAMP,
			    percentage = %s,
			    total_points = %s
			WHERE attempt_id = %s AND user_id = %s
			""",
			(percentage, total_points, attempt_id, student_id),
		)
		return {
			"test_id": test_id,
			"attempt_id": attempt_id,
			"test_name": test_name,
			"question_count": question_count,
			"correct_count": correct_count,
			"percentage": percentage,
			"total_points": total_points,
			"timed_out": expired,
		}


def _fetch_rows(query, parameters, fields):
	with PostgresConnectionProvider().cursor() as cursor:
		cursor.execute(query, parameters)
		return [dict(zip(fields, row)) for row in cursor.fetchall()]

def row_to_user(row):
    """Maps a users table row to a User domain entity."""
    user_id, email, password_hash, role, is_disabled = row
    return User(
        user_id=user_id,
        email=email,
        password_hash=password_hash,
        role=role,
        is_disabled=is_disabled,
    )
