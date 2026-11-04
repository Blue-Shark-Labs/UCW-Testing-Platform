# Seed one login per role for local/nonprod testing. Never run against prod.
# Run with `make seed-dev-users` (or `python3 -m database.migrations.seed_dev_users`).

from werkzeug.security import generate_password_hash

from database.connection import PostgresConnectionProvider


DEV_USERS = [
    ("Ada", "Admin", "admin@dev.local", "AdminPass123!", "admin"),
    ("Lee", "Lecturer", "lecturer@dev.local", "LecturerPass123!", "lecturer"),
    ("Sam", "Student", "student@dev.local", "StudentPass123!", "student"),
]


def seed_dev_users():
    provider = PostgresConnectionProvider()
    with provider.cursor() as cur:
        for first_name, last_name, email, password, role in DEV_USERS:
            cur.execute(
                """
                INSERT INTO users (first_name, last_name, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                RETURNING user_id;
                """,
                (first_name, last_name, email, generate_password_hash(password), role),
            )
            row = cur.fetchone()
            if row and role == "student":
                cur.execute(
                    """
                    INSERT INTO students (user_id, student_number, course_title, is_approved)
                    VALUES (%s, %s, %s, TRUE);
                    """,
                    (row[0], "S0000001", "BSc Computer Science"),
                )
    print("Dev users seeded.")


if __name__ == "__main__":
    seed_dev_users()
