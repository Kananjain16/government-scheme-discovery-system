
import csv
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(
    BASE_DIR,
    "rag_evaluation_results.csv"
)


def to_int(value):

    if value is None or str(value).strip() == "":
        return None

    try:
        number = int(value)

        if number not in (0, 1):
            return None

        return number

    except ValueError:
        return None


def calculate_percentage(rows, column):

    values = [
        to_int(row.get(column))
        for row in rows
    ]

    values = [
        value for value in values
        if value is not None
    ]

    if not values:
        return None

    return sum(values) / len(values) * 100


def calculate_metrics():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        rows = list(csv.DictReader(file))

    reviewed = [
        row for row in rows
        if to_int(row.get("answer_correct")) is not None
    ]

    if not reviewed:

        print("No reviewed answers found.")
        print("Review the CSV first.")
        return

    correctness = calculate_percentage(
        rows,
        "answer_correct"
    )

    groundedness = calculate_percentage(
        rows,
        "answer_grounded"
    )

    completeness = calculate_percentage(
        rows,
        "answer_complete"
    )

    hallucination_rate = calculate_percentage(
        rows,
        "hallucination_found"
    )

    print("\n" + "=" * 60)
    print("RAG EVALUATION METRICS")
    print("=" * 60)

    print("Total Test Questions:", len(rows))
    print("Reviewed Questions:", len(reviewed))

    print("\nAnswer Quality:")

    def display(name, value):

        if value is None:
            print(name + ": Not available")
        else:
            print(f"{name}: {value:.2f}%")

    display("Answer Correctness", correctness)
    display("Groundedness", groundedness)
    display("Completeness", completeness)
    display("Hallucination Rate", hallucination_rate)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    calculate_metrics()
