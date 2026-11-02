
from pathlib import Path
import sys
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Allow access to the existing database connection module.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from database.db import get_connection


ARTIFACT_DIR = PROJECT_ROOT / "backend" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = ARTIFACT_DIR / "tfidf_vectorizer.joblib"
MATRIX_PATH = ARTIFACT_DIR / "tfidf_matrix.joblib"
DOCUMENTS_PATH = ARTIFACT_DIR / "tfidf_documents.joblib"


def fetch_documents():

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
                d.processed_text
            FROM schemes s
            JOIN scheme_search_documents d
                ON s.scheme_id = d.scheme_id
            WHERE d.processed_text IS NOT NULL
              AND TRIM(d.processed_text) != ''
        """)

        return cursor.fetchall()

    finally:
        conn.close()


def build_index():

    documents = fetch_documents()

    if not documents:
        raise ValueError("No processed scheme documents found.")

    texts = [doc["processed_text"] for doc in documents]

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95,
        sublinear_tf=True
    )

    tfidf_matrix = vectorizer.fit_transform(texts)

    joblib.dump(vectorizer, MODEL_PATH)
    joblib.dump(tfidf_matrix, MATRIX_PATH)
    joblib.dump(documents, DOCUMENTS_PATH)

    print("TF-IDF index created successfully.")
    print("Number of documents:", len(documents))
    print("Vocabulary size:", len(vectorizer.vocabulary_))
    print("Matrix shape:", tfidf_matrix.shape)


def search_schemes(query, top_k=10):

    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty.")

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k must be a positive integer.")

    # Check whether all index artifacts exist.
    if not all([
        MODEL_PATH.exists(),
        MATRIX_PATH.exists(),
        DOCUMENTS_PATH.exists()
    ]):
        raise FileNotFoundError(
            "TF-IDF index not found. Build the index first."
        )

    vectorizer = joblib.load(MODEL_PATH)
    tfidf_matrix = joblib.load(MATRIX_PATH)
    documents = joblib.load(DOCUMENTS_PATH)

    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(
        query_vector,
        tfidf_matrix
    ).flatten()

    ranked_indices = scores.argsort()[::-1]

    results = []

    for index in ranked_indices:

        score = float(scores[index])
        if score <= 0:
            continue

        doc = documents[index]

        results.append({
            "scheme_id": doc["scheme_id"],
            "scheme_name": doc["scheme_name"],
            "level": doc["level"],
            "benefits": doc["benefits"],
            "eligibility": doc["eligibility"],
            "score": round(score, 4)
        })

        if len(results) >= top_k:
            break

    return results


if __name__ == "__main__":

    build_index()

    while True:

        query = input("\nEnter your search query (or 'exit'): ")

        if query.strip().lower() == "exit":
            break

        try:
            results = search_schemes(query)

            if not results:
                print("No matching schemes found.")
                continue

            for rank, result in enumerate(results, start=1):

                print(f"\nRank: {rank}")
                print("Scheme:", result["scheme_name"])
                print("Level:", result["level"])
                print("Score:", result["score"])
                print("Benefits:", result["benefits"])

        except ValueError as error:
            print(error)
