
from app.rag.rag_pipeline import answer_question


def test_rag():

    question = ("What is the mobile number of the officer "
    "responsible for approving applications?"
    )
    print("\n" + "=" * 70)

    print("\nUSER QUESTION:")
    print(question)

    try:

        result = answer_question(
            question=question,
            scheme_id=101,
            top_k=5
        )

        print("\nGENERATED ANSWER:")
        print(result["answer"])

        print("\nSOURCE REFERENCES:")

        if not result["sources"]:
            print("No sources found.")

        for source in result["sources"]:

            print("-" * 50)

            print("Scheme:", source["scheme_name"])
            print("Scheme ID:", source["scheme_id"])
            print("Section:", source["section_name"])
            print("Chunk ID:", source["chunk_id"])
            print("Similarity:", source["similarity_score"])

    except Exception as error:

        print("\nERROR:")
        print(str(error))


if __name__ == "__main__":
    test_rag()
