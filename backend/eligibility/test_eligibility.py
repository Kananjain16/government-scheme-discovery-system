from eligibility.eligibility_rules import (
    evaluate_condition,
    match_scheme_eligibility
)


def test_individual_conditions():

    occupation_condition = {
        "field_name": "occupation",
        "operator": "equals",
        "value_text": "student"
    }

    assert evaluate_condition(
        occupation_condition,
        {"occupation": "student"}
    ) is True

    assert evaluate_condition(
        occupation_condition,
        {"occupation": "farmer"}
    ) is False

    age_condition = {
        "field_name": "age",
        "operator": "between",
        "min_value": 18,
        "max_value": 30
    }

    assert evaluate_condition(
        age_condition,
        {"age": 22}
    ) is True

    assert evaluate_condition(
        age_condition,
        {"age": 35}
    ) is False

    assert evaluate_condition(
        age_condition,
        {}
    ) is None


def test_scheme_matching():

    conditions = [
        {
            "field_name": "occupation",
            "operator": "equals",
            "value_text": "student",
            "is_mandatory": True,
            "verification_status": "verified"
        },
        {
            "field_name": "age",
            "operator": "between",
            "min_value": 18,
            "max_value": 30,
            "is_mandatory": True,
            "verification_status": "verified"
        }
    ]

    # All conditions pass
    result = match_scheme_eligibility(
        conditions,
        {"occupation": "student", "age": 22}
    )

    assert result["status"] == "potentially_eligible"

    # One mandatory condition fails
    result = match_scheme_eligibility(
        conditions,
        {"occupation": "farmer", "age": 22}
    )

    assert result["status"] == "not_eligible"

    # Missing information
    result = match_scheme_eligibility(
        conditions,
        {"occupation": "student"}
    )

    assert result["status"] == "needs_verification"

    # Pending condition
    conditions[0]["verification_status"] = "pending"

    result = match_scheme_eligibility(
        conditions,
        {"occupation": "student", "age": 22}
    )

    assert result["status"] == "needs_verification"

    # No conditions
    result = match_scheme_eligibility([], {})

    assert result["status"] == "needs_verification"


if __name__ == "__main__":
    test_individual_conditions()
    test_scheme_matching()

    print("All eligibility matching tests passed!")
