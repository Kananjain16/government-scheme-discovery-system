
import re

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from backend.database.db import get_connection

stop_words = set(stopwords.words("english"))

important_words = {
    "no", "not", "nor", "never",
    "without", "only", "must",
    "above", "below", "under",
    "over", "between", "minimum",
    "maximum", "less", "more"
}

stop_words = stop_words - important_words

lemmatizer = WordNetLemmatizer()

def generate_raw_text(scheme):

    fields = {
        "Scheme Name": scheme["scheme_name"],
        "Details": scheme["details"],
        "Benefits": scheme["benefits"],
        "Eligibility": scheme["eligibility"],
        "Application Process": scheme["application"],
        "Required Documents": scheme["documents"],
        "Level": scheme["level"],
        "Category": scheme["schemeCategory"],
        "Tags": scheme["tags"]
    }

    parts = []

    for label, value in fields.items():

        if value is not None and str(value).strip():

            parts.append(f"{label}: {str(value).strip()}")

    return "\n".join(parts)


def preprocess_text(text):

    text = text.lower()

    tokens = re.findall(r"[a-z]+|\d+(?:\.\d+)?", text)

    processed_tokens = []

    for token in tokens:

        if token in stop_words:
            continue

        if token.isalpha():
            token = lemmatizer.lemmatize(token)

        processed_tokens.append(token)

    return " ".join(processed_tokens)


def process_schemes():

    conn = get_connection()

    cursor = conn.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                scheme_id,
                scheme_name,
                details,
                benefits,
                eligibility,
                application,
                documents,
                level,
                schemeCategory,
                tags
            FROM schemes
        """)

        schemes = cursor.fetchall()

        print("Total schemes fetched:", len(schemes))

        processed_count = 0

        for scheme in schemes:

            raw_text = generate_raw_text(scheme)

            processed_text = preprocess_text(raw_text)

            cursor.execute("""
                INSERT INTO scheme_search_documents
                (scheme_id, raw_text, processed_text)

                VALUES (%s, %s, %s)

                ON DUPLICATE KEY UPDATE
                    raw_text = VALUES(raw_text),
                    processed_text = VALUES(processed_text)

            """, (
                scheme["scheme_id"],
                raw_text,
                processed_text
            ))

            processed_count += 1

        conn.commit()

        print("\nPreprocessing completed!")
        print("Records processed:", processed_count)

    except Exception as e:

        conn.rollback()

        print("Error during preprocessing:", e)

        raise

    finally:

        cursor.close()
        conn.close()
if __name__ == "__main__":

    process_schemes()
