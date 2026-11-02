from backend.database.db import get_connection


def generate_raw_text():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM schemes")

    schemes = cursor.fetchall()

    for scheme in schemes:

        raw_text = f"""
        Scheme Name: {scheme.get('scheme_name', '')}

        Description: {scheme.get('description', '')}

        Eligibility: {scheme.get('eligibility', '')}

        Benefits: {scheme.get('benefits', '')}

        Application Process: {scheme.get('application_process', '')}
        """

        cursor.execute("""
            INSERT INTO scheme_search_documents
            (scheme_id, raw_text)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
            raw_text = VALUES(raw_text)
        """, (scheme['scheme_id'], raw_text.strip()))

    conn.commit()

    cursor.close()
    conn.close()

    print("Raw scheme documents generated successfully!")


if __name__ == "__main__":
    generate_raw_text()