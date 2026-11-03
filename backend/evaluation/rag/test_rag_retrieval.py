
import csv
import os
import json

from app.rag.rag_retriever import retrieve_relevant_chunks


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(BASE_DIR, "rag_test_queries.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "rag_retrieval_results.csv")


def evaluate_retrieval():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        test_cases = list(csv.DictReader(file))

    results = []

    for test in test_cases:

        test_id = test["test_id"]
        question = test["question"]
        expected_section = test["expected_section"].strip().lower()
        scheme_id = test["scheme_id"].strip()

        print("\n" + "=" * 75)
        print("TEST ID:", test_id)
        print("QUESTION:", question)

        try:

            retrieved_chunks = retrieve_relevant_chunks(
                query=question,
                scheme_id=int(scheme_id) if scheme_id else None,
                top_k=5
            )

            if not retrieved_chunks:
                retrieved_chunks = []

            retrieved_sections = []
            chunk_details = []

            for rank, chunk in enumerate(retrieved_chunks, start=1):

                section = str(
                    chunk.get("section_name", "")
                ).strip().lower()

                retrieved_sections.append(section)

                details = {
                    "rank": rank,
                    "chunk_id": chunk.get("chunk_id"),
                    "scheme_id": chunk.get("scheme_id"),
                    "scheme_name": chunk.get("scheme_name"),
                    "section_name": chunk.get("section_name"),
                    "similarity_score": chunk.get("similarity_score"),
                    "chunk_text": chunk.get("chunk_text")
                }

                chunk_details.append(details)

                print("\nRank:", rank)
                print("Chunk ID:", details["chunk_id"])
                print("Scheme ID:", details["scheme_id"])
                print("Scheme Name:", details["scheme_name"])
                print("Section:", details["section_name"])
                print("Similarity:", details["similarity_score"])
                print("Chunk Text:", details["chunk_text"])

            if expected_section == "unknown":
                section_hit = "NOT_APPLICABLE"

            elif expected_section:
                section_hit = int(
                    expected_section in retrieved_sections
                )

            else:
                section_hit = "NOT_SPECIFIED"

            print("\nExpected Section:", expected_section)
            print("Section Hit@5:", section_hit)

            results.append({
                "test_id": test_id,
                "question": question,
                "expected_section": expected_section,
                "scheme_id": scheme_id,
                "retrieved_count": len(chunk_details),
                "retrieved_sections": json.dumps(retrieved_sections),
                "section_hit_at_5": section_hit,
                "retrieved_chunks": json.dumps(
                    chunk_details,
                    ensure_ascii=False
                ),
                "error": ""
            })

        except Exception as error:

            print("ERROR:", str(error))

            results.append({
                "test_id": test_id,
                "question": question,
                "expected_section": expected_section,
                "scheme_id": scheme_id,
                "retrieved_count": 0,
                "retrieved_sections": "[]",
                "section_hit_at_5": "",
                "retrieved_chunks": "[]",
                "error": str(error)
            })

    fieldnames = [
        "test_id",
        "question",
        "expected_section",
        "scheme_id",
        "retrieved_count",
        "retrieved_sections",
        "section_hit_at_5",
        "retrieved_chunks",
        "error"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 75)
    print("RETRIEVAL EVALUATION COMPLETED")
    print("Results saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    evaluate_retrieval()
