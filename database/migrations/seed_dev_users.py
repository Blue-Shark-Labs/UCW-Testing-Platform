# Seed dev logins and sample students from seed_data/users.json. Never run against prod.
# Run with `make seed-dev-users` (or `python3 -m database.migrations.seed_dev_users`).

from werkzeug.security import generate_password_hash

from database.connection import PostgresConnectionProvider
from database.migrations.seed_data import load_seed_data


def seed_dev_users():
    seed = load_seed_data("users")
    password_hashes = {}
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        for user in seed["users"]:
            password = user.get("password", seed["defaultPassword"])
            if password not in password_hashes:
                password_hashes[password] = generate_password_hash(password)
            # Existing accounts keep their current password and profile.
            cur.execute(
                """
                INSERT INTO users (first_name, last_name, email, password_hash, role, is_disabled)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING;
                """,
                (
                    user["firstName"],
                    user["lastName"],
                    user["email"],
                    password_hashes[password],
                    user["role"],
                    user.get("isDisabled", False),
                ),
            )
            student = user.get("student")
            if student is None:
                continue
            cur.execute("SELECT user_id FROM users WHERE email = %s;", (user["email"],))
            user_id = cur.fetchone()[0]
            cur.execute(
                """
                INSERT INTO students (user_id, student_number, course_title, is_approved)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING;
                """,
                (user_id, student["studentNumber"], student["courseTitle"], student["isApproved"]),
            )
    print(f"Seeded {len(seed['users'])} dev users.")


if __name__ == "__main__":
    seed_dev_users()
