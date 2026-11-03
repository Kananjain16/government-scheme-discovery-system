
import json

import numpy as np

from sentence_transformers import SentenceTransformer

from database.db import get_connection


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Load model once instead of loading it for every query.
_model = None


def load_model():

    global _model

    if _model is None:

        _model = SentenceTransformer(MODEL_NAME)

    return _model


def retrieve_relevant_chunks(
    query,
    top_k=5,
    scheme_id=None
):
    """
    Retrieve the most relevant scheme document chunks.

    query: User's question.
    top_k: Number of relevant chunks to return.
    scheme_id: Optional scheme filter.
    """

    if not query or not query.strip():

        raise ValueError("Query cannot be empty")

    if not isinstance(top_k, int) or top_k <= 0:

        raise ValueError("top_k must be a positive integer")

    model = load_model()

    # ---------------------------------
    # STEP 1: Generate query embedding
    # ---------------------------------

    query_embedding = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # ---------------------------------
    # STEP 2: Retrieve stored chunks
    # ---------------------------------

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    try:

        base_query = """
            SELECT
                c.chunk_id,
                c.scheme_id,
                s.scheme_name,
                c.chunk_index,
                c.section_name,
                c.chunk_text,
                c.embedding_json,
                c.model_name

            FROM scheme_document_chunks c

            JOIN schemes s
                ON c.scheme_id = s.scheme_id
        """

        if scheme_id is not None:

            base_query += """
                WHERE c.scheme_id = %s
            """

            cursor.execute(
                base_query,
                (scheme_id,)
            )

        else:

            cursor.execute(base_query)

        stored_chunks = cursor.fetchall()

    finally:

        cursor.close()
        connection.close()

    if not stored_chunks:

        return []

    # ---------------------------------
    # STEP 3: Calculate similarity
    # ---------------------------------

    results = []

    for chunk in stored_chunks:

        if not chunk["embedding_json"]:

            continue

        if chunk["model_name"] != MODEL_NAME:

            continue

        stored_embedding = np.array(
            json.loads(chunk["embedding_json"]),
            dtype=np.float32
        )

        if stored_embedding.shape != query_embedding.shape:

            continue

        # Both embeddings are normalized.
        # Dot product = cosine similarity.

        similarity = float(
            np.dot(query_embedding, stored_embedding)
        )

        results.append({

            "chunk_id": chunk["chunk_id"],

            "scheme_id": chunk["scheme_id"],

            "scheme_name": chunk["scheme_name"],

            "chunk_index": chunk["chunk_index"],

            "section_name": chunk["section_name"],

            "chunk_text": chunk["chunk_text"],

            "similarity_score": similarity

        })

    # ---------------------------------
    # STEP 4: Rank results
    # ---------------------------------

    results.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return results[:top_k]
