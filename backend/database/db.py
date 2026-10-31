
import sqlite3
from pathlib import Path

# Get the database directory
BASE_DIR = Path(__file__).resolve().parent

# Database file path
DB_PATH = BASE_DIR / "government_schemes.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS schemes (
            scheme_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_name TEXT NOT NULL,
            category TEXT,
            government_level TEXT,
            state TEXT,
            description TEXT,
            eligibility_text TEXT,
            min_age INTEGER,
            max_age INTEGER,
            income_limit REAL,
            occupation TEXT,
            education TEXT,
            benefits TEXT,
            required_documents TEXT,
            application_process TEXT,
            source_url TEXT,
            last_verified TEXT
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Database and tables created successfully!")
