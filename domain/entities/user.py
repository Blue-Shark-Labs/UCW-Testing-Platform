# User entity definition. To be used as a representation of a user within the domain layer.

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    user_id: str
    email: str
    password_hash: str
    role: str
    is_disabled: bool
    # Only students can be unapproved; other roles are always True.
    is_approved: bool = True


@dataclass(frozen=True)
class StudentRegistration:
    first_name: str
    last_name: str
    email: str
    student_number: str
    course_title: str
    password: str
