
from database.db import get_connection


def get_scheme_conditions(scheme_id):

    connection = get_connection()
    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                condition_id,
                scheme_id,
                field_name,
                operator,
                value_text,
                min_value,
                max_value,
                is_mandatory,
                verification_status
            FROM scheme_eligibility_conditions
            WHERE scheme_id = %s
            ORDER BY condition_id
        """

        cursor.execute(query, (scheme_id,))

        conditions = cursor.fetchall()

        return conditions

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()
