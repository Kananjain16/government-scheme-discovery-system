
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.retrieval.semantic_search import search_semantic

QUERY_FILE = PROJECT_ROOT / "dataset" / "test_queries.csv"
OUTPUT_FILE = PROJECT_ROOT / "dataset" / "semantic_results.csv"


def generate_results():

    with open(QUERY_FILE, "r", encoding="utf-8") as file:
        queries = list(csv.DictReader(file))

    rows = []

    for item in queries:
        query = item["query"]

        print("Searching:", query)

        results = search_semantic(query, top_k=10)

        for rank, result in enumerate(results, start=1):
            rows.append({
                "query": query,
                "rank": rank,
                "scheme_id": result["scheme_id"],
                "scheme_name": result["scheme_name"],
                "score": result["score"]
            })

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "query",
                "rank",
                "scheme_id",
                "scheme_name",
                "score"
            ]
        )

        writer.writeheader()
        writer.writerows(rows)

    print("\nSemantic results generated successfully.")
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    generate_results()
