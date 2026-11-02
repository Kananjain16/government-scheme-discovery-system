
import re

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from backend.database.db import get_connection


# ---------------------------------
# 1. Initialize NLP tools
# ---------------------------------

stop_words = set(stopwords.words("english"))

# Preserve words that affect eligibility and conditions.
important_words = {
    "no", "not", "nor", "never",
    "without", "only", "must",
    "above", "below", "under",
    "over", "between", "minimum",
    "maximum", "less", "more"
}

stop_words = stop_words - important_words

lemmatizer = WordNetLemmatizer()


# ---------------------------------
# 2. Combine scheme information
# ---------------------------------

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


# ---------------------------------
# 3. Text preprocessing
# ---------------------------------

def preprocess_text(text):

    # Convert to lowercase
    text = text.lower()

    # Extract words and numbers.
    # Numbers are preserved for age and income limits.
    tokens = re.findall(r"[a-z]+|\d+(?:\.\d+)?", text)

    processed_tokens = []

    for token in tokens:

        # Remove common stop words
        if token in stop_words:
            continue

        # Lemmatize words
        if token.isalpha():
            token = lemmatizer.lemmatize(token)

        processed_tokens.append(token)

    return " ".join(processed_tokens)


# ---------------------------------
# 4. Fetch and process schemes
# ---------------------------------

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

            # Generate original combined text
            raw_text = generate_raw_text(scheme)

            # Generate normalized text
            processed_text = preprocess_text(raw_text)

            # Insert or update existing document
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


# ---------------------------------
# 5. Main execution
# ---------------------------------

if __name__ == "__main__":

    process_schemes()
