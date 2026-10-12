import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    password = os.getenv("POSTGRES_PASSWORD")

    if not password:
        raise RuntimeError(
            "POSTGRES_PASSWORD is missing. Check your .env file."
        )

    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "lenny"),
        user=os.getenv("POSTGRES_USER", "lenny"),
        password=password,
        connect_timeout=5,
        row_factory=dict_row,
    )


if __name__ == "__main__":
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT current_database() AS database_name"
                )
                result = cursor.fetchone()

        print(
            "Database connected successfully:",
            result["database_name"],
        )

    except (psycopg.Error, RuntimeError, ValueError):
        print(
            "Database connection failed. Check Docker, the .env "
            "password, and the database host and port."
        )
        raise SystemExit(1)