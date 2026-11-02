
import pandas as pd
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_FILE = BASE_DIR / "dataset" / "OriginalDataset.csv"
OUTPUT_FILE = BASE_DIR / "dataset" / "cleaned_schemes.csv"
REPORT_DIR = BASE_DIR / "dataset" / "reports"
def clean_dataset():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig"
    )

    print("\nOriginal dataset information")
    print("--------------------------------")
    print("Total records:", len(df))
    print("Total columns:", len(df.columns))


    df.columns = df.columns.str.strip()


    # --------------------------------
    # 4. Remove completely empty columns
    # --------------------------------

    empty_columns = df.columns[
        df.isna().all()
    ].tolist()

    print("\nEmpty columns:", empty_columns)

    df = df.dropna(axis=1, how="all")


    # --------------------------------
    # 5. Clean text fields
    # --------------------------------

    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for col in text_columns:

        df[col] = df[col].apply(
            lambda x: x.strip()
            if isinstance(x, str)
            else x
        )


    # --------------------------------
    # 6. Convert empty strings to missing values
    # --------------------------------

    df = df.replace(
        r"^\s*$",
        pd.NA,
        regex=True
    )


    # --------------------------------
    # 7. Validate required columns
    # --------------------------------

    required_columns = [
        "scheme_name",
        "slug",
        "details",
        "benefits",
        "eligibility",
        "application",
        "documents",
        "level",
        "schemeCategory",
        "tags"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )


    # --------------------------------
    # 8. Identify duplicate scheme names
    # --------------------------------

    duplicate_names = df[
        df.duplicated(
            subset=["scheme_name"],
            keep=False
        )
    ].sort_values("scheme_name")

    duplicate_names.to_csv(
        REPORT_DIR / "duplicate_names.csv",
        index=False
    )

    print("\nDuplicate scheme names:", len(duplicate_names))


    # --------------------------------
    # 9. Identify duplicate slugs
    # --------------------------------

    duplicate_slugs = df[
        df.duplicated(
            subset=["slug"],
            keep=False
        )
    ].sort_values("slug")

    duplicate_slugs.to_csv(
        REPORT_DIR / "duplicate_slugs.csv",
        index=False
    )

    print("Duplicate slug records:", len(duplicate_slugs))


    # --------------------------------
    # 10. Check missing values
    # --------------------------------

    missing_report = pd.DataFrame({
        "column": df.columns,
        "missing_count": [
            df[col].isna().sum()
            for col in df.columns
        ]
    })

    missing_report.to_csv(
        REPORT_DIR / "missing_values.csv",
        index=False
    )

    print("\nMissing values:")
    print(missing_report.to_string(index=False))


    # --------------------------------
    # 11. Check government levels
    # --------------------------------

    print("\nGovernment level distribution:")

    print(
        df["level"].value_counts(dropna=False)
    )


    # --------------------------------
    # 12. Add source tracking columns
    # --------------------------------

    if "source_url" not in df.columns:
        df["source_url"] = pd.NA

    if "source_name" not in df.columns:
        df["source_name"] = pd.NA


    # --------------------------------
    # 13. Save cleaned dataset
    # --------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n--------------------------------")
    print("DATASET CLEANING COMPLETED")
    print("--------------------------------")

    print("Original records:", 3400)
    print("Cleaned records:", len(df))
    print("Cleaned columns:", len(df.columns))
    print("Output file:", OUTPUT_FILE)
    print("Reports folder:", REPORT_DIR)


if __name__ == "__main__":
    clean_dataset()
