
import logging

from flask import Blueprint, request, jsonify

from backend.app.retrieval.semantic_search import search_semantic
from backend.app.discovery import discover_schemes
from backend.eligibility.eligibility_rules import match_scheme_eligibility
from backend.eligibility.eligibility_service import get_scheme_conditions
from backend.app.rag.rag_pipeline import answer_question
from backend.app.rag.llm_client import GeminiServiceError


logger = logging.getLogger(__name__)

search_bp = Blueprint("search", __name__)


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

    try:
        results = search_semantic(query, top_k=10)

        return jsonify({
            "success": True,
            "query": query,
            "method": "semantic",
            "total_results": len(results),
            "results": results
        }), 200

    except FileNotFoundError:

        logger.exception("Semantic search index not found.")

        return jsonify({
            "success": False,
            "message": "Semantic search index not found."
        }), 503

    except Exception:

        logger.exception("Error occurred during semantic search.")

        return jsonify({
            "success": False,
            "message": "An internal error occurred while searching."
        }), 500


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


@search_bp.route("/api/discover", methods=["POST"])
def discover():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "A valid JSON request body is required."
        }), 400

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

        result = discover_schemes(
            query=query,
            profile=profile,
            top_k=top_k
        )

        return jsonify({
            "success": True,
            "message": "Scheme discovery completed successfully.",
            "data": result
        }), 200

    except FileNotFoundError:

        logger.exception("Semantic discovery index not found.")

        return jsonify({
            "success": False,
            "message": "Required search index not found."
        }), 503

    except ValueError as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 400

    except Exception:

        logger.exception("Scheme discovery failed.")

        return jsonify({
            "success": False,
            "message": "An internal error occurred during scheme discovery."
        }), 500


@search_bp.route("/api/rag/ask", methods=["POST"])
def ask_rag():

    try:

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "error": "Request body must be valid JSON."
            }), 400

        question = data.get("question")
        scheme_id = data.get("scheme_id")
        top_k = data.get("top_k", 5)

        if not isinstance(question, str) or not question.strip():
            return jsonify({
                "success": False,
                "error": "A non-empty question is required."
            }), 400

        question = question.strip()

        if scheme_id is not None:

            if (
                isinstance(scheme_id, bool)
                or not isinstance(scheme_id, int)
                or scheme_id <= 0
            ):
                return jsonify({
                    "success": False,
                    "error": "scheme_id must be a positive integer."
                }), 400

        if (
            isinstance(top_k, bool)
            or not isinstance(top_k, int)
            or top_k < 1
            or top_k > 20
        ):
            return jsonify({
                "success": False,
                "error": "top_k must be an integer between 1 and 20."
            }), 400

        result = answer_question(
            question=question,
            scheme_id=scheme_id,
            top_k=top_k
        )

        answer = result.get("answer", "")
        sources = result.get("sources", [])

        return jsonify({
            "success": True,
            "question": question,
            "answer": answer,
            "sources": sources,
            "context_found": len(sources) > 0
        }), 200

    except GeminiServiceError as error:

        logger.warning(
            "Gemini service error: %s",
            error.user_message
        )

        return jsonify({
            "success": False,
            "error": error.user_message,
            "sources": error.sources
        }), error.status_code

    except ValueError as error:

        logger.warning(
            "Invalid RAG request: %s",
            str(error)
        )

        return jsonify({
            "success": False,
            "error": str(error),
            "sources": []
        }), 400

    except Exception:

        logger.exception("RAG API failed.")

        return jsonify({
            "success": False,
            "error": "An unexpected error occurred while processing the RAG request.",
            "sources": []
        }), 500
