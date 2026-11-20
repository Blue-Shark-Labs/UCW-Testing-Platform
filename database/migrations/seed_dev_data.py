"""Import the JSON users and subjects into a local development database."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

ROOT_DIR = Path(__file__).resolve().parents[2]


USERS_FILE = ROOT_DIR / "data" / "users.json"
SUBJECTS_FILE = ROOT_DIR / "data" / "subjects.json"
PLACEHOLDER_PASSWORD_HASH = "REPLACE_WITH_BCRYPT_HASH"


def load_records(path: Path, collection: str) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object.")

    records = data.get(collection)
    if not isinstance(records, list) or not all(
        isinstance(record, dict) for record in records
    ):
        raise ValueError(f"{path.name} must contain a '{collection}' list of objects.")

    return records


def parse_last_login(value: str | None, email: str) -> datetime | None:
    if value in (None, "", "n/a"):
        return None
    if not isinstance(value, str):
        raise ValueError(f"Invalid lastLoginAt for user {email}.")

    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"Invalid lastLoginAt for user {email}.") from error


def seed_dev_data() -> None:
    load_dotenv(ROOT_DIR / "dev.env")
    from database.connection import PostgresConnectionProvider

    users = load_records(USERS_FILE, "users")
    subjects = load_records(SUBJECTS_FILE, "subjects")

    placeholder_users = [
        user for user in users
        if user.get("passwordHash") == PLACEHOLDER_PASSWORD_HASH
    ]
    seed_password = os.environ.get("DEV_SEED_PASSWORD")
    if placeholder_users and not seed_password:
        raise ValueError(
            "Set DEV_SEED_PASSWORD to a local development password before seeding "
            "users with placeholder password hashes."
        )
    generated_password_hash = (
        generate_password_hash(seed_password) if placeholder_users else None
    )

    provider = PostgresConnectionProvider()
    user_ids: dict[int, uuid.UUID] = {}
    seen_emails: set[str] = set()
    missing_lecturer_ids: set[int] = set()
    imported_assignments = 0
    subject_uuids: list[uuid.UUID] = []

    with provider.cursor() as cur:
        for user in users:
            legacy_id = user.get("userId")
            if not isinstance(legacy_id, int) or isinstance(legacy_id, bool):
                raise ValueError("Every JSON user must have an integer userId.")
            if legacy_id in user_ids:
                raise ValueError(f"Duplicate userId in users.json: {legacy_id}.")

            first_name = user.get("firstName", "")
            last_name = user.get("lastName", "")
            email = user.get("email", "")
            role = user.get("role", "")
            if not isinstance(first_name, str) or not first_name or len(first_name) > 50:
                raise ValueError(f"Invalid firstName for userId {legacy_id}.")
            if not isinstance(last_name, str) or not last_name or len(last_name) > 50:
                raise ValueError(f"Invalid lastName for userId {legacy_id}.")
            if not isinstance(email, str) or not email or len(email) > 50:
                raise ValueError(f"Invalid email for userId {legacy_id}.")
            if email in seen_emails:
                raise ValueError(f"Duplicate email in users.json: {email}.")
            seen_emails.add(email)
            if not isinstance(role, str) or role not in {"student", "lecturer", "admin"}:
                raise ValueError(f"Invalid role for userId {legacy_id}: {role!r}.")
            if role == "student":
                raise ValueError(
                    f"User {email} is a student, but users.json has no student "
                    "number or course data required by the students table."
                )

            password_hash = user.get("passwordHash", "")
            if password_hash == PLACEHOLDER_PASSWORD_HASH:
                password_hash = generated_password_hash
            if not isinstance(password_hash, str) or not password_hash:
                raise ValueError(f"Missing passwordHash for user {email}.")

            mfa_secret = user.get("mfaSecret")
            if mfa_secret is not None and (
                not isinstance(mfa_secret, str) or len(mfa_secret) > 64
            ):
                raise ValueError(f"Invalid mfaSecret for user {email}.")
            mfa_enabled = user.get("mfaEnabled", False)
            is_disabled = user.get("isDisabled", False)
            if not isinstance(mfa_enabled, bool) or not isinstance(is_disabled, bool):
                raise ValueError(f"Invalid account flags for user {email}.")

            stable_user_id = uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"ucw-testing-platform:dev-user:{legacy_id}",
            )
            cur.execute(
                """
                INSERT INTO users (
                    user_id, first_name, last_name, email, password_hash, role,
                    mfa_enabled, mfa_secret, is_disabled, last_login_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    password_hash = EXCLUDED.password_hash,
                    role = EXCLUDED.role,
                    mfa_enabled = EXCLUDED.mfa_enabled,
                    mfa_secret = EXCLUDED.mfa_secret,
                    is_disabled = EXCLUDED.is_disabled,
                    last_login_at = EXCLUDED.last_login_at
                RETURNING user_id;
                """,
                (
                    stable_user_id,
                    first_name,
                    last_name,
                    email,
                    password_hash,
                    role,
                    mfa_enabled,
                    mfa_secret,
                    is_disabled,
                    parse_last_login(user.get("lastLoginAt"), email),
                ),
            )
            user_ids[legacy_id] = cur.fetchone()[0]

        for subject in subjects:
            raw_subject_id = subject.get("subjectId")
            if not isinstance(raw_subject_id, str):
                raise ValueError("Every subject must have a valid subjectId UUID.")
            try:
                subject_id = uuid.UUID(raw_subject_id)
            except ValueError as error:
                raise ValueError("Every subject must have a valid subjectId UUID.") from error

            if subject_id in subject_uuids:
                raise ValueError(f"Duplicate subjectId in subjects.json: {subject_id}.")
            subject_uuids.append(subject_id)

            name = subject.get("name", "")
            description = subject.get("description")
            if not isinstance(name, str) or not name or len(name) > 100:
                raise ValueError(f"Invalid name for subjectId {subject_id}.")
            if description is not None and (
                not isinstance(description, str) or len(description) > 250
            ):
                raise ValueError(f"Description is too long for subject {subject_id}.")
            is_active = subject.get("isActive", True)
            if not isinstance(is_active, bool):
                raise ValueError(f"Invalid isActive value for subject {subject_id}.")

            cur.execute(
                """
                INSERT INTO subjects (subject_id, name, description, is_active)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (subject_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    is_active = EXCLUDED.is_active;
                """,
                (subject_id, name, description, is_active),
            )
            cur.execute(
                "DELETE FROM subject_lecturers WHERE subject_id = %s;",
                (subject_id,),
            )

            lecturer_ids = subject.get("lecturers", [])
            if not isinstance(lecturer_ids, list):
                raise ValueError(f"Lecturers must be a list for subject {subject_id}.")

            for lecturer_id in lecturer_ids:
                if not isinstance(lecturer_id, int) or isinstance(lecturer_id, bool):
                    raise ValueError(
                        f"Invalid lecturer ID in subject {subject_id}: {lecturer_id!r}."
                    )

                user_id = user_ids.get(lecturer_id)
                if user_id is None:
                    missing_lecturer_ids.add(lecturer_id)
                    continue

                cur.execute(
                    """
                    INSERT INTO subject_lecturers (subject_id, user_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    (subject_id, user_id),
                )
                imported_assignments += 1

    ignored_subject_fields = sorted({
        field
        for subject in subjects
        for field in ("code", "updatedAt")
        if field in subject
    })
    print(
        f"Seeded {len(users)} users, {len(subjects)} subjects, and "
        f"{imported_assignments} lecturer assignments."
    )
    if ignored_subject_fields:
        print(
            "Not imported because they are not columns in the database schema: "
            + ", ".join(ignored_subject_fields)
        )
    if missing_lecturer_ids:
        print(
            "Skipped lecturer assignments for user IDs missing from users.json: "
            + ", ".join(str(user_id) for user_id in sorted(missing_lecturer_ids))
        )


if __name__ == "__main__":
    seed_dev_data()
