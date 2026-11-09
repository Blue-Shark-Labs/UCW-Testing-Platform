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
	"""Return tests assigned to a student that they have not completed."""
	fields = ("test_id", "test_name", "subject_name", "question_count", "assigned_at")
	query = """
		SELECT t.test_id, t.title, s.name, t.question_count, a.assigned_at
		FROM test_assignments AS a
		JOIN tests AS t ON t.test_id = a.test_id
		JOIN subjects AS s ON s.subject_id = t.subject_id
		WHERE a.student_id = %s
		  AND NOT EXISTS (
			  SELECT 1
			  FROM test_attempts AS attempt
			  WHERE attempt.test_id = a.test_id
				AND attempt.user_id = a.student_id
				AND attempt.completed_at IS NOT NULL
		  )
		ORDER BY a.assigned_at DESC, t.title
	"""
	return _fetch_rows(query, (student_id,), fields)


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


def get_active_subjects():
	"""Return active subjects for the leaderboard selector."""
	fields = ("subject_id", "name")
	query = """
		SELECT subject_id, name
		FROM subjects
		WHERE is_active = TRUE
		ORDER BY name
	"""
	return _fetch_rows(query, (), fields)


def get_subject_leaderboard(subject_id):
	"""Return the five highest-scoring students for a subject."""
	fields = (
		"user_id",
		"first_name",
		"last_name",
		"completed_test_count",
		"average_percentage",
		"total_points",
	)
	query = """
		SELECT u.user_id, u.first_name, u.last_name,
			   COUNT(*) AS completed_test_count,
			   ROUND(AVG(attempt.percentage), 1) AS average_percentage,
			   SUM(COALESCE(attempt.total_points, 0)) AS total_points
		FROM test_attempts AS attempt
		JOIN tests AS t ON t.test_id = attempt.test_id
		JOIN users AS u ON u.user_id = attempt.user_id
		JOIN students AS student ON student.user_id = u.user_id
		WHERE t.subject_id = %s
		  AND attempt.completed_at IS NOT NULL
		  AND u.role = 'student'
		  AND u.is_disabled = FALSE
		  AND student.is_approved = TRUE
		GROUP BY u.user_id, u.first_name, u.last_name
		ORDER BY total_points DESC, average_percentage DESC,
				 u.last_name, u.first_name, u.user_id
		LIMIT 5
	"""
	return _fetch_rows(query, (subject_id,), fields)


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
