from app.retrieval.semantic_search import search_semantic
from eligibility.eligibility_rules import match_scheme_eligibility
from eligibility.eligibility_service import get_scheme_conditions
def discover_schemes(query, profile, top_k=10):

    candidates = search_semantic(query, top_k=top_k)
    potentially_eligible = []
    needs_verification = []
    not_eligible = []
    for rank, scheme in enumerate(candidates, start=1):

        scheme_id = scheme["scheme_id"]

        conditions = get_scheme_conditions(scheme_id)

        eligibility = match_scheme_eligibility(
            conditions,
            profile
        )

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

    return {
        "query": query,
        "retrieval_method": "semantic",
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
