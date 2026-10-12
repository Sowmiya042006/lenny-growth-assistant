from uuid import uuid4

from psycopg.types.json import Jsonb

from database import get_connection


def create_session(title="New chat", user_metadata=None):
    session_id = uuid4()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO chat_sessions (id, title, user_metadata)
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                (
                    session_id,
                    title,
                    Jsonb(user_metadata or {}),
                ),
            )
            return cursor.fetchone()


def list_sessions():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM chat_sessions
                ORDER BY updated_at DESC, id
                LIMIT 100
                """
            )
            return cursor.fetchall()


def get_session(session_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM chat_sessions WHERE id = %s",
                (session_id,),
            )
            return cursor.fetchone()


def get_messages(session_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM chat_messages
                WHERE session_id = %s
                ORDER BY id
                """,
                (session_id,),
            )
            return cursor.fetchall()


def save_exchange(
    session_id,
    question,
    answer,
    model,
    sources,
    grounding_status,
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            # Lock this session while saving the exchange.
            cursor.execute(
                """
                SELECT id
                FROM chat_sessions
                WHERE id = %s
                FOR UPDATE
                """,
                (session_id,),
            )

            if cursor.fetchone() is None:
                raise ValueError("Chat session does not exist.")

            cursor.execute(
                """
                INSERT INTO chat_messages (session_id, role, content)
                VALUES (%s, 'user', %s)
                """,
                (session_id, question),
            )

            cursor.execute(
                """
                INSERT INTO chat_messages (
                    session_id, role, content, model,
                    sources, grounding_status
                )
                VALUES (%s, 'assistant', %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    session_id,
                    answer,
                    model,
                    Jsonb(sources),
                    grounding_status,
                ),
            )
            saved_answer = cursor.fetchone()

            cursor.execute(
                """
                UPDATE chat_sessions
                SET updated_at = CURRENT_TIMESTAMP,
                    title = CASE
                        WHEN title = 'New chat' THEN %s
                        ELSE title
                    END
                WHERE id = %s
                """,
                (question[:80], session_id),
            )

            return saved_answer

def delete_session(session_id):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            # Delete the session's messages first.
            cursor.execute(
                """
                DELETE FROM chat_messages
                WHERE session_id = %s
                """,
                (session_id,),
            )

            cursor.execute(
                """
                DELETE FROM chat_sessions
                WHERE id = %s
                RETURNING id
                """,
                (session_id,),
            )

            return cursor.fetchone() is not None