
import csv
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULTS_FILE = PROJECT_ROOT / "dataset" / "tfidf_results.csv"
JUDGMENTS_FILE = (
    PROJECT_ROOT / "dataset" / "relevance_judgments_final.csv"
)
SUMMARY_FILE = PROJECT_ROOT / "dataset" / "tfidf_evaluation_summary.csv"


def load_results():

    results = defaultdict(list)

    with open(RESULTS_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            query = row["query"]
            scheme_id = row["scheme_id"]

            results[query].append(scheme_id)

    return results


def load_judgments():

    judgments = defaultdict(set)

    with open(JUDGMENTS_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:

            query = row["query"]
            scheme_id = row["scheme_id"]
            relevant = int(row["relevant"])

            if relevant not in (0, 1):
                raise ValueError("Relevance must be 0 or 1.")

            if relevant == 1:
                judgments[query].add(scheme_id)

    return judgments


def precision_at_k(ranked_ids, relevant_ids, k):

    top_k = ranked_ids[:k]

    if not top_k:
        return 0.0

    relevant_count = sum(
        1 for scheme_id in top_k
        if scheme_id in relevant_ids
    )

    return relevant_count / k


def recall_at_k(ranked_ids, relevant_ids, k):

    if not relevant_ids:
        return 0.0

    top_k = ranked_ids[:k]

    relevant_count = sum(
        1 for scheme_id in top_k
        if scheme_id in relevant_ids
    )

    return relevant_count / len(relevant_ids)


def average_precision(ranked_ids, relevant_ids):

    if not relevant_ids:
        return 0.0

    hits = 0
    precision_sum = 0.0

    for rank, scheme_id in enumerate(ranked_ids, start=1):

        if scheme_id in relevant_ids:

            hits += 1
            precision_sum += hits / rank

    return precision_sum / len(relevant_ids)


def reciprocal_rank(ranked_ids, relevant_ids):

    for rank, scheme_id in enumerate(ranked_ids, start=1):

        if scheme_id in relevant_ids:
            return 1.0 / rank

    return 0.0


def evaluate():

    results = load_results()
    judgments = load_judgments()

    queries = sorted(set(results) | set(judgments))

    if not queries:
        raise ValueError("No queries found.")

    summary_rows = []

    p_values = []
    r_values = []
    ap_values = []
    rr_values = []

    for query in queries:

        ranked_ids = results.get(query, [])
        relevant_ids = judgments.get(query, set())

        p = precision_at_k(ranked_ids, relevant_ids, 5)
        r = recall_at_k(ranked_ids, relevant_ids, 5)
        ap = average_precision(ranked_ids, relevant_ids)
        rr = reciprocal_rank(ranked_ids, relevant_ids)

        p_values.append(p)
        r_values.append(r)
        ap_values.append(ap)
        rr_values.append(rr)

        summary_rows.append({
            "query": query,
            "precision@5": round(p, 4),
            "recall@5": round(r, 4),
            "average_precision": round(ap, 4),
            "reciprocal_rank": round(rr, 4)
        })

        print("\nQuery:", query)
        print("Relevant schemes:", len(relevant_ids))
        print("Precision@5:", round(p, 4))
        print("Recall@5:", round(r, 4))
        print("Average Precision:", round(ap, 4))
        print("Reciprocal Rank:", round(rr, 4))

    count = len(queries)

    overall = {
        "query": "OVERALL",
        "precision@5": round(sum(p_values) / count, 4),
        "recall@5": round(sum(r_values) / count, 4),
        "average_precision": round(sum(ap_values) / count, 4),
        "reciprocal_rank": round(sum(rr_values) / count, 4)
    }

    summary_rows.append(overall)

    with open(
        SUMMARY_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "query",
                "precision@5",
                "recall@5",
                "average_precision",
                "reciprocal_rank"
            ]
        )

        writer.writeheader()
        writer.writerows(summary_rows)

    print("\n========== OVERALL RESULTS ==========")
    print("Number of queries:", count)
    print("Mean Precision@5:", overall["precision@5"])
    print("Mean Recall@5:", overall["recall@5"])
    print("MAP:", overall["average_precision"])
    print("MRR:", overall["reciprocal_rank"])

    print("\nSummary saved:", SUMMARY_FILE)


if __name__ == "__main__":
    evaluate()
