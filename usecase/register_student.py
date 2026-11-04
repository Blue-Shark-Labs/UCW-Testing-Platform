# Use case: register a new student account pending lecturer approval.

from werkzeug.security import generate_password_hash

from database.login.student_registration import create_student

MIN_PASSWORD_LENGTH = 8

# Limits mirror the column sizes in database/migrations/migrate.py.
FIELD_LIMITS = {
    "first_name": ("First name", 50),
    "last_name": ("Last name", 50),
    "email": ("Email", 50),
    "student_number": ("Student number", 20),
    "course_title": ("Course title", 100),
}


def validate_registration(registration):
    """Returns a list of validation error messages (empty when valid)."""
    errors = []
    for field, (label, max_length) in FIELD_LIMITS.items():
        value = getattr(registration, field)
        if not value:
            errors.append(f"{label} is required.")
        elif len(value) > max_length:
            errors.append(f"{label} must be {max_length} characters or fewer.")

    if registration.email and "@" not in registration.email:
        errors.append("Email must be a valid email address.")

    if not registration.password:
        errors.append("Password is required.")
    elif len(registration.password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")

    return errors


def register_student(connection_provider, registration):
    """Validates and stores a student with a hashed password. Returns a list of errors."""
    errors = validate_registration(registration)
    if errors:
        return errors

    password_hash = generate_password_hash(registration.password)
    if not create_student(connection_provider, registration, password_hash):
        return ["An account with this email already exists."]
    return []
