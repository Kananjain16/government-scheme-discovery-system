
from backend.database.db import get_connection


try:

    conn = get_connection()

    if conn.is_connected():

        print("MySQL connected successfully!")

        print(
            "Database:",
            conn.database
        )

    conn.close()


except Exception as e:

    print("Database connection failed:", e)
