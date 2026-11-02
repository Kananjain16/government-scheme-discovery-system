import json
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from database.db import get_connection


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

BATCH_SIZE = 32


def fetch_documents():
    conn = get_connection()

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                scheme_id,
                COALESCE(
                    NULLIF(TRIM(raw_text), ''),
                    processed_text
                ) AS document_text
            FROM scheme_search_documents
            WHERE (
                raw_text IS NOT NULL
                AND TRIM(raw_text) != ''
            )
            OR (
                processed_text IS NOT NULL
                AND TRIM(processed_text) != ''
            )
        """)

        return cursor.fetchall()

    finally:
        conn.close()


def save_embeddings(documents, embeddings):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        query = """
            INSERT INTO scheme_embeddings
                (scheme_id, model_name, embedding_json)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                model_name = VALUES(model_name),
                embedding_json = VALUES(embedding_json)
        """

        values = []

        for doc, embedding in zip(documents, embeddings):
            values.append((
                doc["scheme_id"],
                MODEL_NAME,
                json.dumps(embedding.tolist())
            ))

        cursor.executemany(query, values)
        conn.commit()

        print("Embeddings saved:", len(values))

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
        cursor.close()


def generate_embeddings():
    documents = fetch_documents()

    if not documents:
        raise ValueError("No scheme documents found.")

    texts = [doc["document_text"] for doc in documents]

    print("Loading embedding model:", MODEL_NAME)

    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    print("Embedding shape:", embeddings.shape)

    save_embeddings(documents, embeddings)

    print("Embedding generation completed successfully.")


if __name__ == "__main__":
    generate_embeddings()
