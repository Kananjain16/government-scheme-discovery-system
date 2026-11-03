
import csv
import os
import json


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RETRIEVAL_FILE = os.path.join(
    BASE_DIR,
    "rag_retrieval_results.csv"
)

JUDGMENT_FILE = os.path.join(
    BASE_DIR,
    "chunk_relevance_judgments.csv"
)


def evaluate_chunk_relevance():

    with open(
        RETRIEVAL_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        retrieval_rows = list(csv.DictReader(file))

    with open(
        JUDGMENT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        judgment_rows = list(csv.DictReader(file))

    judgments = {}

    for row in judgment_rows:

        test_id = row["test_id"].strip()
        chunk_id = row["chunk_id"].strip()
        relevance = row["relevance"].strip()

        if not test_id or not chunk_id:
            continue

        if relevance not in ("0", "1"):
            continue

        judgments[(test_id, chunk_id)] = int(relevance)

    total_precision = 0
    total_rr = 0
    evaluated_queries = 0

    print("\n" + "=" * 70)
    print("CHUNK RETRIEVAL EVALUATION")
    print("=" * 70)

    for row in retrieval_rows:

        test_id = row["test_id"]

        try:
            chunks = json.loads(
                row["retrieved_chunks"]
            )
        except (ValueError, TypeError):
            chunks = []

        top_chunks = chunks[:5]

        judged_chunks = []

        for rank, chunk in enumerate(top_chunks, start=1):

            chunk_id = chunk.get("chunk_id")

            if chunk_id is None:
                continue

            chunk_id = str(chunk_id)

            key = (test_id, chunk_id)

            if key in judgments:

                judged_chunks.append({
                    "rank": rank,
                    "chunk_id": chunk_id,
                    "relevance": judgments[key]
                })

        if not judged_chunks:

            print("\nTest ID:", test_id)
            print("Skipped: No relevance judgments.")
            continue

        relevant_count = sum(
            item["relevance"]
            for item in judged_chunks
        )

        precision = relevant_count / len(judged_chunks)

        relevant_ranks = [
            item["rank"]
            for item in judged_chunks
            if item["relevance"] == 1
        ]

        if relevant_ranks:

            reciprocal_rank = 1 / min(relevant_ranks)

        else:

            reciprocal_rank = 0

        total_precision += precision
        total_rr += reciprocal_rank
        evaluated_queries += 1

        print("\nTest ID:", test_id)
        print("Question:", row["question"])
        print("Judged Chunks:", len(judged_chunks))
        print("Relevant Chunks:", relevant_count)
        print("Precision@5 (judged):", round(precision, 4))
        print("Reciprocal Rank:", round(reciprocal_rank, 4))

        if len(judged_chunks) < len(top_chunks):
            print(
                "WARNING: Some retrieved chunks are unjudged."
            )

    print("\n" + "=" * 70)

    if evaluated_queries:

        precision_at_5 = total_precision / evaluated_queries
        mrr = total_rr / evaluated_queries

        print("Evaluated Queries:", evaluated_queries)

        print(
            "Mean Precision@5 (judged):",
            round(precision_at_5, 4)
        )

        print(
            "Mean Reciprocal Rank (MRR):",
            round(mrr, 4)
        )

    else:

        print("No queries had relevance judgments.")

    print("=" * 70)


if __name__ == "__main__":
    evaluate_chunk_relevance()
