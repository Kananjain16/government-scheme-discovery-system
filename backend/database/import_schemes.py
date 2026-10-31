
import pandas as pd
from pathlib import Path

from backend.database.connection import get_connection


# Project root
ROOT = Path(__file__).resolve().parents[2]

# Cleaned dataset path
CSV_PATH = ROOT / "dataset" / "cleaned_schemes.csv"


def import_schemes():

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {CSV_PATH}"
        )

    # Read CSV
    df = pd.read_csv(
        CSV_PATH,
        encoding="utf-8-sig"
    )

    # Required columns in MySQL
    columns = [
        "scheme_name",
        "slug",
        "details",
        "benefits",
        "eligibility",
        "application",
        "documents",
        "level",
        "schemeCategory",
        "tags",
        "source_url",
        "source_name"
    ]

    # Check missing columns
    missing = [
        col for col in columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing CSV columns: {missing}"
        )

    # Remove rows without scheme names
    df = df.dropna(subset=["scheme_name"])

    # Convert pandas missing values to Python None
    df = df[columns].astype(object)
    df = df.where(pd.notna(df), None)

    # Convert records into tuples
    data = list(
        df.itertuples(index=False, name=None)
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # Prevent accidental repeated imports
        cursor.execute(
            "SELECT COUNT(*) FROM schemes"
        )

        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            raise RuntimeError(
                "Schemes table is not empty. "
                "Import cancelled to prevent duplicates."
            )

        query = """
            INSERT INTO schemes (
                scheme_name,
                slug,
                details,
                benefits,
                eligibility,
                application,
                documents,
                level,
                schemeCategory,
                tags,
                source_url,
                source_name
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """

        # Insert records in batches
        batch_size = 500

        for start in range(0, len(data), batch_size):

            batch = data[start:start + batch_size]

            cursor.executemany(query, batch)

            print(
                f"Inserted {min(start + batch_size, len(data))} "
                f"of {len(data)} records"
            )

        conn.commit()

        print("\nImport completed successfully!")
        print("Total records imported:", len(data))

    except Exception:

        conn.rollback()
        raise

    finally:

        cursor.close()
        conn.close()


if __name__ == "__main__":
    import_schemes()
