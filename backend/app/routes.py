
import logging

from flask import Blueprint, request, jsonify

from app.retrieval.tfidf_search import search_schemes
from app.retrieval.semantic_search import search_semantic

from app.discovery import discover_schemes

from eligibility.eligibility_rules import match_scheme_eligibility
from eligibility.eligibility_service import get_scheme_conditions

logger = logging.getLogger(__name__)

search_bp = Blueprint("search", __name__)


# ==========================================
# SEARCH API
# ==========================================

@search_bp.route("/api/search", methods=["GET"])
def search():

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "success": False,
            "message": "Search query is required."
        }), 400

    if len(query) > 500:
        return jsonify({
            "success": False,
            "message": "Search query is too long."
        }), 400

    method = request.args.get("method", "tfidf").lower()

    if method not in ("tfidf", "semantic"):
        return jsonify({
            "success": False,
            "message": "Method must be tfidf or semantic."
        }), 400

    try:

        if method == "semantic":
            results = search_semantic(query, top_k=10)
        else:
            results = search_schemes(query, top_k=10)

        return jsonify({
            "success": True,
            "query": query,
            "method": method,
            "total_results": len(results),
            "results": results
        }), 200

    except FileNotFoundError:

        logger.exception("Search index not found.")

        return jsonify({
            "success": False,
            "message": "Search index not found."
        }), 503

    except Exception:

        logger.exception("Error occurred during scheme search.")

        return jsonify({
            "success": False,
            "message": "An internal error occurred while searching."
        }), 500


# ==========================================
# ELIGIBILITY CHECK API
# ==========================================

@search_bp.route("/api/eligibility/check", methods=["POST"])
def check_eligibility():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "A valid JSON request body is required."
        }), 400

    scheme_id = data.get("scheme_id")

    if scheme_id is None:
        return jsonify({
            "success": False,
            "message": "scheme_id is required."
        }), 400

    try:

        if isinstance(scheme_id, bool):
            raise ValueError()

        scheme_id = int(scheme_id)

        if scheme_id <= 0:
            raise ValueError()

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "scheme_id must be a positive integer."
        }), 400

    profile = data.get("profile")

    if not isinstance(profile, dict):
        return jsonify({
            "success": False,
            "message": "A profile object is required."
        }), 400

    allowed_fields = {
        "age",
        "annual_income",
        "state",
        "occupation",
        "gender",
        "category"
    }

    if set(profile.keys()) - allowed_fields:
        return jsonify({
            "success": False,
            "message": "Profile contains unsupported fields."
        }), 400

    for field in ("age", "annual_income"):

        value = profile.get(field)

        if value is not None:

            if isinstance(value, bool):
                return jsonify({
                    "success": False,
                    "message": f"{field} must be numeric."
                }), 400

            try:
                profile[field] = float(value)

            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": f"{field} must be numeric."
                }), 400

            if profile[field] < 0:
                return jsonify({
                    "success": False,
                    "message": f"{field} cannot be negative."
                }), 400

    try:

        conditions = get_scheme_conditions(scheme_id)

        result = match_scheme_eligibility(
            conditions,
            profile
        )

        return jsonify({
            "success": True,
            "scheme_id": scheme_id,
            "result": result
        }), 200

    except Exception:

        logger.exception(
            "Eligibility check failed for scheme %s",
            scheme_id
        )

        return jsonify({
            "success": False,
            "message": "An error occurred while checking eligibility."
        }), 500


# ==========================================
# SCHEME DISCOVERY API
# ==========================================

@search_bp.route("/api/discover", methods=["POST"])
def discover():

    data = request.get_json(silent=True)

    # 1. Validate request body
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "A valid JSON request body is required."
        }), 400

    # 2. Validate query
    query = data.get("query")

    if not isinstance(query, str) or not query.strip():
        return jsonify({
            "success": False,
            "message": "Search query is required."
        }), 400

    query = query.strip()

    if len(query) > 500:
        return jsonify({
            "success": False,
            "message": "Search query is too long."
        }), 400

    # 3. Validate retrieval method
    method = data.get("method", "tfidf")

    if not isinstance(method, str):
        return jsonify({
            "success": False,
            "message": "Method must be tfidf or semantic."
        }), 400

    method = method.lower().strip()

    if method not in ("tfidf", "semantic"):
        return jsonify({
            "success": False,
            "message": "Method must be tfidf or semantic."
        }), 400

    # 4. Validate top_k
    top_k = data.get("top_k", 10)

    if (
        isinstance(top_k, bool)
        or not isinstance(top_k, int)
        or not 1 <= top_k <= 50
    ):
        return jsonify({
            "success": False,
            "message": "top_k must be between 1 and 50."
        }), 400

    # 5. Validate profile
    profile = data.get("profile", {})

    if not isinstance(profile, dict):
        return jsonify({
            "success": False,
            "message": "Profile must be a JSON object."
        }), 400

    allowed_fields = {
        "age",
        "annual_income",
        "state",
        "occupation",
        "gender",
        "category"
    }

    if set(profile.keys()) - allowed_fields:
        return jsonify({
            "success": False,
            "message": "Profile contains unsupported fields."
        }), 400

    # 6. Validate numeric fields
    for field in ("age", "annual_income"):

        value = profile.get(field)

        if value is not None:

            if isinstance(value, bool):
                return jsonify({
                    "success": False,
                    "message": f"{field} must be numeric."
                }), 400

            try:
                profile[field] = float(value)

            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": f"{field} must be numeric."
                }), 400

            if profile[field] < 0:
                return jsonify({
                    "success": False,
                    "message": f"{field} cannot be negative."
                }), 400

    # 7. Run discovery engine
    try:

        result = discover_schemes(
            query=query,
            profile=profile,
            method=method,
            top_k=top_k
        )

        return jsonify({
            "success": True,
            "message": "Scheme discovery completed successfully.",
            "data": result
        }), 200

    except FileNotFoundError:

        logger.exception("Discovery index not found.")

        return jsonify({
            "success": False,
            "message": "Required search index not found."
        }), 503

    except ValueError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400

    except Exception:

        logger.exception("Scheme discovery failed.")

        return jsonify({
            "success": False,
            "message": "An internal error occurred during scheme discovery."
        }), 500
