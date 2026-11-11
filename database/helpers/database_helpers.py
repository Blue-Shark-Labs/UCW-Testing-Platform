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
		WHERE NOT EXISTS (
			  SELECT 1
			  FROM test_attempts AS attempt
			  WHERE attempt.test_id = t.test_id
				AND attempt.user_id = %s
				AND attempt.completed_at IS NOT NULL
		  )
		ORDER BY t.title
	"""
	return _fetch_rows(query, (student_id,), fields)


def get_completed_tests(student_id):
	"""Return completed attempts with their result summary for a student."""
	fields = (
		"attempt_id",
		"test_id",
		"test_name",
		"subject_name",
		"completed_at",
		"question_count",
		"percentage",
		"total_points",
	)
	query = """
		SELECT attempt.attempt_id, t.test_id, t.title, s.name,
			   attempt.completed_at,
			   COUNT(DISTINCT answer.question_id), attempt.percentage,
			   attempt.total_points
		FROM test_attempts AS attempt
		JOIN tests AS t ON t.test_id = attempt.test_id
		JOIN subjects AS s ON s.subject_id = t.subject_id
		LEFT JOIN attempt_answers AS answer ON answer.attempt_id = attempt.attempt_id
		WHERE attempt.user_id = %s
		  AND attempt.completed_at IS NOT NULL
		GROUP BY attempt.attempt_id, t.test_id, t.title, s.name
		ORDER BY attempt.completed_at DESC
	"""
	return _fetch_rows(query, (student_id,), fields)


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
