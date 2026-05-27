import pathlib
import sys

from dotenv import load_dotenv

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from database.db import get_connection


load_dotenv()


def run_schema():
    schema_path = pathlib.Path(__file__).with_name("schema.sql")
    sql = schema_path.read_text(encoding="utf-8")

    migration_sql = """
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = 'ingredientes_scraper_url_key'
        ) THEN
            ALTER TABLE public.ingredientes_scraper
            DROP CONSTRAINT ingredientes_scraper_url_key;
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = 'ingredientes_scraper_ingrediente_tienda_key'
        ) THEN
            ALTER TABLE public.ingredientes_scraper
            ADD CONSTRAINT ingredientes_scraper_ingrediente_tienda_key UNIQUE (ingrediente, tienda);
        END IF;
    END $$;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(migration_sql)

    print("Schema executed successfully")


if __name__ == "__main__":
    run_schema()
