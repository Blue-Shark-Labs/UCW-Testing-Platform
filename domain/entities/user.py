# User entity definition. To be used as a representation of a user within the domain layer.

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    user_id: str
    email: str
    password_hash: str
    role: str
    is_disabled: bool
    is_locked: bool = False
