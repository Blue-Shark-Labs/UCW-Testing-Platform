from database.helpers.database_helpers import submit_expired_test_attempts


if __name__ == "__main__":
    print(f"Submitted {submit_expired_test_attempts()} expired test attempt(s).")
