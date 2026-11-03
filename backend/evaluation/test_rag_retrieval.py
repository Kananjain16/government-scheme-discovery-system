from app.rag.rag_retriever import retrieve_relevant_chunks


def test_retrieval():

    test_queries = [

        "What are the benefits provided under government schemes?",

        "What documents are required to apply for a government scheme?",

        "What are the eligibility criteria for farmers?",

        "How can someone apply for a government scheme?",

        "Which schemes provide financial assistance to senior citizens?"

    ]

    for query in test_queries:

        print("\n" + "=" * 80)

        print("USER QUERY:", query)

        print("=" * 80)

        results = retrieve_relevant_chunks(
            query=query,
            top_k=5
        )

        if not results:

            print("No relevant chunks found.")

            continue

        for rank, result in enumerate(results, start=1):

            print(f"\nRank: {rank}")

            print("Scheme ID:", result["scheme_id"])

            print("Section:", result["section_name"])

            print(
                "Similarity Score:",
                round(result["similarity_score"], 4)
            )

            print("Retrieved Text:")

            print(result["chunk_text"])

            print("-" * 80)


if __name__ == "__main__":

    test_retrieval()