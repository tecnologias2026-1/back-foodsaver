# import email

from psycopg2 import errors

from database.db import get_connection


class DuplicateEmailError(Exception):
    pass

def get_all_ingredients():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, nombre, precio, tienda, url, fecha FROM ingredientes_scraper ORDER BY id ASC"
            )
            return cur.fetchall()


def create_ingredient(nombre: str, precio, tienda: str, url: str):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ingredientes_scraper (nombre, precio, tienda, url) VALUES (%s, %s, %s, %s) RETURNING id, nombre, precio, tienda, url, fecha",
                    (nombre, precio, tienda, url),
                )
                return cur.fetchone()
    except errors.UniqueViolation as exc:
        raise DuplicateEmailError("email already exists") from exc


def update_ingredient(ingredient_id: int, nombre: str, precio, tienda: str, url: str):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ingredientes_scraper SET nombre = %s, precio = %s, tienda = %s, url = %s WHERE id = %s RETURNING id, nombre, precio, tienda, url, fecha",
                    (nombre, precio, tienda, url, ingredient_id),
                )
                return cur.fetchone()
    except errors.UniqueViolation as exc:
        raise DuplicateEmailError("email already exists") from exc


def delete_ingredient(ingredient_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ingredientes_scraper WHERE id = %s RETURNING id", (ingredient_id,))
            return cur.fetchone() is not None
