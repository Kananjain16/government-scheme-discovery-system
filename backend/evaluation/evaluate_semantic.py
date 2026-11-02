
import csv
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULTS_FILE = PROJECT_ROOT / "dataset" / "semantic_results.csv"
JUDGMENTS_FILE = (
    PROJECT_ROOT / "dataset" / "relevance_judgments.csv"
)


def load_results():
    results = defaultdict(list)

    with open(RESULTS_FILE, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            results[row["query"]].append(int(row["scheme_id"]))

    return results


def load_judgments():
    judgments = defaultdict(set)

    with open(JUDGMENTS_FILE, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if int(row["relevant"]) == 1:
                judgments[row["query"]].add(int(row["scheme_id"]))

    return judgments


def precision_at_k(ranked_ids, relevant_ids, k):
    top_k = ranked_ids[:k]

    if not top_k:
        return 0.0

    relevant_count = sum(
        scheme_id in relevant_ids
        for scheme_id in top_k
    )

    # Standard P@K uses K as the denominator.
    return relevant_count / k


def recall_at_k(ranked_ids, relevant_ids, k):
    if not relevant_ids:
        return 0.0

    relevant_count = sum(
        scheme_id in relevant_ids
        for scheme_id in ranked_ids[:k]
    )

    return relevant_count / len(relevant_ids)


def average_precision(ranked_ids, relevant_ids):
    if not relevant_ids:
        return 0.0

    relevant_found = 0
    precision_sum = 0.0

    for rank, scheme_id in enumerate(ranked_ids, start=1):
        if scheme_id in relevant_ids:
            relevant_found += 1
            precision_sum += relevant_found / rank

    return precision_sum / len(relevant_ids)


def reciprocal_rank(ranked_ids, relevant_ids):
    for rank, scheme_id in enumerate(ranked_ids, start=1):
        if scheme_id in relevant_ids:
            return 1.0 / rank

    return 0.0


def evaluate():

    results = load_results()
    judgments = load_judgments()

    queries = sorted(judgments.keys())

    if not queries:
        raise ValueError("No relevance judgments found.")

    p_values = []
    r_values = []
    ap_values = []
    rr_values = []

    for query in queries:

        relevant_ids = judgments[query]
        ranked_ids = results.get(query, [])

        if not relevant_ids:
            raise ValueError(
                f"No relevant schemes judged for query: {query}"
            )

        p = precision_at_k(ranked_ids, relevant_ids, 5)
        r = recall_at_k(ranked_ids, relevant_ids, 5)
        ap = average_precision(ranked_ids, relevant_ids)
        rr = reciprocal_rank(ranked_ids, relevant_ids)

        p_values.append(p)
        r_values.append(r)
        ap_values.append(ap)
        rr_values.append(rr)

        print("\nQuery:", query)
        print("Precision@5:", round(p, 4))
        print("Recall@5:", round(r, 4))
        print("Average Precision:", round(ap, 4))
        print("Reciprocal Rank:", round(rr, 4))

    count = len(queries)

    print("\n========== SEMANTIC SEARCH RESULTS ==========")
    print("Number of queries:", count)
    print("Mean Precision@5:", round(sum(p_values) / count, 4))
    print("Mean Recall@5:", round(sum(r_values) / count, 4))
    print("MAP:", round(sum(ap_values) / count, 4))
    print("MRR:", round(sum(rr_values) / count, 4))


if __name__ == "__main__":
    evaluate()
