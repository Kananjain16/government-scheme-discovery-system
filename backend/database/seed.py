import csv
from pathlib import Path

from db import get_connection, create_tables

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "updated_data.csv"

TEST_LIMIT = None


def clean(value):
    """Convert empty CSV values into None."""
    if value is None:
        return None

    value = value.strip()

    return value if value else None


def insert_sample_data():

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV file not found: {CSV_PATH}"
        )

    # Ensure database and table exist
    create_tables()

    conn = get_connection()

    inserted = 0
    skipped = 0

    try:
        with open(
            CSV_PATH,
            mode="r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                scheme_name = clean(row.get("scheme_name"))

                if not scheme_name:
                    skipped += 1
                    continue

                # Avoid duplicate scheme records
                existing = conn.execute(
                    """
                    SELECT scheme_id
                    FROM schemes
                    WHERE scheme_name = ?
                    """,
                    (scheme_name,)
                ).fetchone()

                if existing:
                    skipped += 1
                    continue

                scheme = (
                    scheme_name,
                    clean(row.get("schemeCategory")),
                    clean(row.get("level")),
                    None,  # State not available in CSV
                    clean(row.get("details")),
                    clean(row.get("eligibility")),
                    None,  # min_age
                    None,  # max_age
                    None,  # income_limit
                    None,  # occupation
                    None,  # education
                    clean(row.get("benefits")),
                    clean(row.get("documents")),
                    clean(row.get("application")),
                    None,  # source_url
                    None   # last_verified
                )

                conn.execute(
                    """
                    INSERT INTO schemes (
                        scheme_name,
                        category,
                        government_level,
                        state,
                        description,
                        eligibility_text,
                        min_age,
                        max_age,
                        income_limit,
                        occupation,
                        education,
                        benefits,
                        required_documents,
                        application_process,
                        source_url,
                        last_verified
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?)
                    """,
                    scheme
                )

                inserted += 1

                if TEST_LIMIT is not None and inserted >= TEST_LIMIT:
                    break

        conn.commit()

        print("Scheme data insertion completed!")
        print(f"Records inserted: {inserted}")
        print(f"Records skipped: {skipped}")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    insert_sample_data()
