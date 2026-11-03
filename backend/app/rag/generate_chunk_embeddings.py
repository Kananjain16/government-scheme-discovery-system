from database.db import get_connection

from app.rag.chunking import split_into_chunks

from app.rag.document_store import (
    delete_scheme_chunks,
    save_chunks
)

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def generate_chunks():

    print("\nLoading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    print("Embedding model loaded successfully.")

    # ---------------------------------
    # STEP 1: Retrieve schemes from MySQL
    # ---------------------------------

    connection = get_connection()

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                scheme_id,
                scheme_name,
                details,
                benefits,
                eligibility,
                documents,
                application
            FROM schemes
            """
        )

        schemes = cursor.fetchall()

    finally:

        cursor.close()
        connection.close()

    print(f"\nTotal schemes retrieved: {len(schemes)}")

    total_chunks = 0

    total_embeddings = 0

    # ---------------------------------
    # STEP 2: Process each scheme
    # ---------------------------------

    for scheme_number, scheme in enumerate(schemes, start=1):

        scheme_id = scheme["scheme_id"]

        scheme_name = scheme["scheme_name"]

        print(
            f"\nProcessing {scheme_number}/{len(schemes)}: "
            f"{scheme_name}"
        )

        # Organize information by section

        sections = {

            "details": scheme.get("details"),

            "benefits": scheme.get("benefits"),

            "eligibility": scheme.get("eligibility"),

            "documents": scheme.get("documents"),

            "application": scheme.get("application")

        }

        # Delete old chunks for this scheme.
        # This ensures that rerunning the script does not
        # leave outdated chunks behind.

        delete_scheme_chunks(scheme_id)

        chunk_index = 0

        scheme_chunk_count = 0

        # ---------------------------------
        # STEP 3: Split information
        # ---------------------------------

        for section_name, content in sections.items():

            if content is None or not str(content).strip():

                continue

            chunks = split_into_chunks(
                content,
                chunk_size=CHUNK_SIZE,
                overlap=CHUNK_OVERLAP
            )

            if not chunks:

                continue

            # ---------------------------------
            # STEP 4: Generate embeddings
            # ---------------------------------

            embeddings = model.encode(
                chunks,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            # ---------------------------------
            # STEP 5: Save chunks and embeddings
            # ---------------------------------

            save_chunks(
                scheme_id=scheme_id,
                section_name=section_name,
                chunks=chunks,
                embeddings=embeddings,
                start_index=chunk_index
            )

            chunk_index += len(chunks)

            scheme_chunk_count += len(chunks)

            total_embeddings += len(embeddings)

        total_chunks += scheme_chunk_count

        print(
            f"Chunks generated for this scheme: "
            f"{scheme_chunk_count}"
        )

    # ---------------------------------
    # STEP 6: Final summary
    # ---------------------------------

    print("\n===================================")

    print("RAG CHUNK GENERATION COMPLETED")

    print("===================================")

    print("Total schemes processed:", len(schemes))

    print("Total chunks generated:", total_chunks)

    print("Total embeddings generated:", total_embeddings)


if __name__ == "__main__":

    generate_chunks()