
from app.retrieval.tfidf_search import search_schemes
from app.retrieval.semantic_search import search_semantic

from eligibility.eligibility_rules import match_scheme_eligibility
from eligibility.eligibility_service import get_scheme_conditions


def discover_schemes(query, profile, method="tfidf", top_k=10):

    # Step 1: Validate retrieval method.
    if method not in ("tfidf", "semantic"):
        raise ValueError("Method must be tfidf or semantic.")

    # Step 2: Retrieve candidate schemes.
    if method == "semantic":
        candidates = search_semantic(query, top_k=top_k)
    else:
        candidates = search_schemes(query, top_k=top_k)

    # Step 3: Prepare result groups.
    potentially_eligible = []
    needs_verification = []
    not_eligible = []

    # Step 4: Evaluate each retrieved scheme.
    for rank, scheme in enumerate(candidates, start=1):

        scheme_id = scheme["scheme_id"]

        # Retrieve actual eligibility conditions.
        conditions = get_scheme_conditions(scheme_id)

        # Pass conditions, NOT scheme_id, to the eligibility engine.
        eligibility = match_scheme_eligibility(
            conditions,
            profile
        )

        # Step 5: Combine retrieval and eligibility information.
        combined_result = {
            "rank": rank,
            "scheme_id": scheme_id,
            "scheme_name": scheme["scheme_name"],
            "level": scheme.get("level"),
            "benefits": scheme.get("benefits"),
            "eligibility_description": scheme.get("eligibility"),
            "retrieval_score": scheme["score"],
            "eligibility": eligibility
        }

        status = eligibility["status"]

        if status == "potentially_eligible":
            potentially_eligible.append(combined_result)

        elif status == "not_eligible":
            not_eligible.append(combined_result)

        else:
            needs_verification.append(combined_result)

    # Step 6: Return discovery results.
    return {
        "query": query,
        "retrieval_method": method,
        "total_retrieved": len(candidates),
        "summary": {
            "potentially_eligible": len(potentially_eligible),
            "needs_verification": len(needs_verification),
            "not_eligible": len(not_eligible)
        },
        "results": {
            "potentially_eligible": potentially_eligible,
            "needs_verification": needs_verification,
            "not_eligible": not_eligible
        }
    }
