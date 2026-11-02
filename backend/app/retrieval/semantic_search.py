
import json
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from database.db import get_connection


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Load the model once, not on every search request.
model = SentenceTransformer(MODEL_NAME)

# Cache the database index in memory.
_index = None


def load_semantic_index():
    global _index

    if _index is not None:
        return _index

    conn = get_connection()

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                s.scheme_id,
                s.scheme_name,
                s.level,
                s.benefits,
                s.eligibility,
                e.embedding_json
            FROM scheme_embeddings e
            JOIN schemes s
                ON e.scheme_id = s.scheme_id
            WHERE e.model_name = %s
        """, (MODEL_NAME,))

        rows = cursor.fetchall()

    finally:
        conn.close()

    if not rows:
        raise ValueError(
            "No embeddings found. Generate embeddings first."
        )

    scheme_embeddings = []
    scheme_documents = []

    for row in rows:
        vector = json.loads(row["embedding_json"])

        scheme_embeddings.append(vector)

        scheme_documents.append({
            "scheme_id": row["scheme_id"],
            "scheme_name": row["scheme_name"],
            "level": row["level"],
            "benefits": row["benefits"],
            "eligibility": row["eligibility"]
        })

    matrix = np.asarray(scheme_embeddings, dtype=np.float32)

    if matrix.ndim != 2 or matrix.shape[1] != 384:
        raise ValueError(
            f"Unexpected embedding matrix shape: {matrix.shape}"
        )

    # The stored embeddings were normalized during generation.
    _index = (matrix, scheme_documents)

    print("Semantic index loaded.")
    print("Documents:", len(scheme_documents))
    print("Matrix shape:", matrix.shape)

    return _index


def search_semantic(query, top_k=10):

    if not query or not query.strip():
        return []

    matrix, documents = load_semantic_index()

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    query_vector = query_embedding[0]

    # Dot product equals cosine similarity because vectors
    # are normalized to unit length.
    scores = np.dot(matrix, query_vector)

    ranked_indices = np.argsort(scores)[::-1][:top_k]

    results = []

    for index in ranked_indices:
        doc = documents[index]

        results.append({
            "scheme_id": doc["scheme_id"],
            "scheme_name": doc["scheme_name"],
            "level": doc["level"],
            "benefits": doc["benefits"],
            "eligibility": doc["eligibility"],
            "score": round(float(scores[index]), 4)
        })

    return results


if __name__ == "__main__":

    while True:
        query = input("\nEnter query (or 'exit'): ")

        if query.strip().lower() == "exit":
            break

        try:
            results = search_semantic(query, top_k=10)

            if not results:
                print("No results found.")
                continue

            for rank, result in enumerate(results, start=1):
                print(f"\nRank: {rank}")
                print("Scheme:", result["scheme_name"])
                print("Score:", result["score"])

        except Exception as error:
            print("Search error:", error)
