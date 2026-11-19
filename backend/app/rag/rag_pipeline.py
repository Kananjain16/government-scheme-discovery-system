
from app.rag.rag_retriever import retrieve_relevant_chunks

from app.rag.prompt_builder import build_rag_prompt

from app.rag.llm_client import generate_answer


def answer_question(
    question,
    scheme_id=None,
    top_k=5
):
    """
    Complete RAG pipeline:

    1. Retrieve relevant document chunks.
    2. Build the prompt.
    3. Send prompt to Gemini.
    4. Generate an answer.
    5. Return answer with source references.
    """
    if not question or not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError(
            "top_k must be a positive integer."
        )
    retrieved_chunks = retrieve_relevant_chunks(
        query=question,
        scheme_id=scheme_id,
        top_k=top_k
    )
    if not retrieved_chunks:

        return {
            "answer": (
                "I could not find relevant scheme "
                "information to answer this question."
            ),
            "sources": []
        }
    prompt = build_rag_prompt(
        question=question,
        retrieved_chunks=retrieved_chunks
    )
    answer = generate_answer(prompt)
    sources = []

    for chunk in retrieved_chunks:

        source = {
            "scheme_name": chunk["scheme_name"],
            "scheme_id": chunk["scheme_id"],
            "section_name": chunk["section_name"],
            "chunk_id": chunk["chunk_id"],
            "similarity_score": float(
                chunk["similarity_score"]
            )
        }

        sources.append(source)
    return {
        "answer": answer,
        "sources": sources
    }
