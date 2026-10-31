
from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.database.db import get_connection, create_tables

app = Flask(__name__)

# Allow frontend applications to communicate with Flask
CORS(app)

# Ensure database table exists
create_tables()


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Government Scheme Discovery System API is running"
    })


@app.route("/api/schemes", methods=["GET"])
def get_schemes():

    conn = get_connection()

    try:
        # Get pagination parameters
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 20, type=int)

        if page < 1 or limit < 1 or limit > 100:
            return jsonify({
                "error": "Invalid page or limit. Limit must be between 1 and 100."
            }), 400

        offset = (page - 1) * limit

        # Fetch schemes
        schemes = conn.execute(
            """
            SELECT *
            FROM schemes
            ORDER BY scheme_id
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        ).fetchall()

        # Count total records
        total = conn.execute(
            "SELECT COUNT(*) FROM schemes"
        ).fetchone()[0]

        result = [dict(row) for row in schemes]

        return jsonify({
            "total_records": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "schemes": result
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)
