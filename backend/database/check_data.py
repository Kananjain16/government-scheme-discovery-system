from db import get_connection

conn = get_connection()

schemes = conn.execute(
    """
    SELECT scheme_id, scheme_name, category,
           government_level, eligibility_text
    FROM schemes
    """
).fetchall()

for scheme in schemes:
    print("--------------------------------")
    print("ID:", scheme["scheme_id"])
    print("Name:", scheme["scheme_name"])
    print("Category:", scheme["category"])
    print("Level:", scheme["government_level"])
    print("Eligibility:", scheme["eligibility_text"])

conn.close()