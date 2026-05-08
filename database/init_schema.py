import pathlib

from dotenv import load_dotenv

from database.db import get_connection


load_dotenv()


def run_schema():
    schema_path = pathlib.Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

    print("Schema executed successfully")


if __name__ == "__main__":
    run_schema()
