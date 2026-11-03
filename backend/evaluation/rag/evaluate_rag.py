
import csv
import os
import json

from app.rag.rag_pipeline import answer_question


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(BASE_DIR, "rag_test_queries.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "rag_evaluation_results.csv")


def get_answer(result):

    if isinstance(result, str):
        return result

    if isinstance(result, dict):

        for key in [
            "answer",
            "generated_answer",
            "response",
            "answer_text"
        ]:
            if result.get(key) is not None:
                return result[key]

    return str(result)


def get_chunks(result):

    if not isinstance(result, dict):
        return []

    for key in [
        "retrieved_chunks",
        "sources",
        "source_chunks",
        "context_chunks",
        "chunks"
    ]:
        value = result.get(key)

        if isinstance(value, list):
            return value

    return []


def evaluate_rag():

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
        scheme_id = test["scheme_id"].strip()

        print("\n" + "=" * 75)
        print("TEST ID:", test_id)
        print("QUESTION:", question)

        try:

            result = answer_question(
                question=question,
                scheme_id=int(scheme_id) if scheme_id else None,
                top_k=5
            )

            answer = get_answer(result)
            chunks = get_chunks(result)

            source_details = []

            for chunk in chunks:

                if not isinstance(chunk, dict):
                    continue

                source_details.append({
                    "chunk_id": chunk.get("chunk_id"),
                    "scheme_id": chunk.get("scheme_id"),
                    "scheme_name": chunk.get("scheme_name"),
                    "section_name": chunk.get("section_name"),
                    "similarity_score": chunk.get("similarity_score"),
                    "chunk_text": chunk.get("chunk_text")
                })

            scheme_names = list(dict.fromkeys(
                str(item["scheme_name"])
                for item in source_details
                if item["scheme_name"] is not None
            ))

            sections = list(dict.fromkeys(
                str(item["section_name"])
                for item in source_details
                if item["section_name"] is not None
            ))

            print("\nGENERATED ANSWER:")
            print(answer)

            print("\nSOURCE SCHEMES:")
            print(scheme_names)

            print("\nSOURCE SECTIONS:")
            print(sections)

            print("\nRETRIEVED CHUNKS:")
            for item in source_details:
                print(json.dumps(item, ensure_ascii=False, indent=2))

            results.append({
                "test_id": test_id,
                "question": question,
                "scheme_id": scheme_id,
                "generated_answer": answer,
                "source_scheme_names": json.dumps(
                    scheme_names,
                    ensure_ascii=False
                ),
                "source_sections": json.dumps(
                    sections,
                    ensure_ascii=False
                ),
                "retrieved_chunks": json.dumps(
                    source_details,
                    ensure_ascii=False
                ),
                "answer_correct": "",
                "answer_grounded": "",
                "answer_complete": "",
                "hallucination_found": "",
                "review_notes": "",
                "error": ""
            })

        except Exception as error:

            print("\nERROR:", str(error))

            results.append({
                "test_id": test_id,
                "question": question,
                "scheme_id": scheme_id,
                "generated_answer": "",
                "source_scheme_names": "[]",
                "source_sections": "[]",
                "retrieved_chunks": "[]",
                "answer_correct": "",
                "answer_grounded": "",
                "answer_complete": "",
                "hallucination_found": "",
                "review_notes": "",
                "error": str(error)
            })

    fieldnames = [
        "test_id",
        "question",
        "scheme_id",
        "generated_answer",
        "source_scheme_names",
        "source_sections",
        "retrieved_chunks",
        "answer_correct",
        "answer_grounded",
        "answer_complete",
        "hallucination_found",
        "review_notes",
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
    print("RAG EVALUATION COMPLETED")
    print("Results saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    evaluate_rag()
