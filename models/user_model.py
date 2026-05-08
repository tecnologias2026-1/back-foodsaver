from psycopg2 import errors

from database.db import get_connection


class DuplicateEmailError(Exception):
    pass


def get_all_users():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, full_name, email, created_at FROM users ORDER BY id ASC"
            )
            return cur.fetchall()


def create_user(full_name: str, email: str):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (full_name, email) VALUES (%s, %s) RETURNING id, full_name, email, created_at",
                    (full_name, email),
                )
                return cur.fetchone()
    except errors.UniqueViolation as exc:
        raise DuplicateEmailError("email already exists") from exc


def update_user(user_id: int, full_name: str, email: str):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET full_name = %s, email = %s WHERE id = %s RETURNING id, full_name, email, created_at",
                    (full_name, email, user_id),
                )
                return cur.fetchone()
    except errors.UniqueViolation as exc:
        raise DuplicateEmailError("email already exists") from exc


def delete_user(user_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s RETURNING id", (user_id,))
            return cur.fetchone() is not None
