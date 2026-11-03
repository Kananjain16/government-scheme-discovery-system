import json

from database.db import get_connection


def delete_scheme_chunks(scheme_id):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM scheme_document_chunks
            WHERE scheme_id = %s
            """,
            (scheme_id,)
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()


def save_chunks(
    scheme_id,
    section_name,
    chunks,
    embeddings,
    start_index=0
):
    """
    Save chunks and their embeddings into MySQL.

    start_index ensures that chunk indexes remain unique
    across different sections of the same scheme.
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks and embeddings must match"
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings),
            start=start_index
        ):

            embedding_json = json.dumps(
                embedding.tolist()
                if hasattr(embedding, "tolist")
                else list(embedding)
            )

            cursor.execute(
                """
                INSERT INTO scheme_document_chunks
                (
                    scheme_id,
                    chunk_index,
                    section_name,
                    chunk_text,
                    embedding_json,
                    model_name
                )
                VALUES (%s, %s, %s, %s, %s, %s)

                ON DUPLICATE KEY UPDATE

                    section_name = VALUES(section_name),
                    chunk_text = VALUES(chunk_text),
                    embedding_json = VALUES(embedding_json),
                    model_name = VALUES(model_name)
                """,
                (
                    scheme_id,
                    index,
                    section_name,
                    chunk,
                    embedding_json,
                    "sentence-transformers/all-MiniLM-L6-v2"
                )
            )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()