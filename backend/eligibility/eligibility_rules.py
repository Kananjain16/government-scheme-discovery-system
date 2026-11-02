
from decimal import Decimal, InvalidOperation

ALLOWED_FIELDS = {
    "age",
    "annual_income",
    "state",
    "occupation",
    "gender",
    "category"
}

ALLOWED_OPERATORS = {
    "equals",
    "not_equals",
    "less_than",
    "less_than_or_equal",
    "greater_than",
    "greater_than_or_equal",
    "between"
}

NUMERIC_FIELDS = {"age", "annual_income"}
TEXT_FIELDS = ALLOWED_FIELDS - NUMERIC_FIELDS

NUMERIC_OPERATORS = {
    "less_than",
    "less_than_or_equal",
    "greater_than",
    "greater_than_or_equal",
    "between"
}


def validate_eligibility_condition(condition):
    if not isinstance(condition, dict):
        raise ValueError("Condition must be a dictionary.")

    field_name = condition.get("field_name")
    operator = condition.get("operator")

    if field_name not in ALLOWED_FIELDS:
        raise ValueError("Unsupported eligibility field.")

    if operator not in ALLOWED_OPERATORS:
        raise ValueError("Unsupported eligibility operator.")

    if field_name in NUMERIC_FIELDS:

        if operator in {"equals", "not_equals"}:
            value = condition.get("min_value")

            if value is None:
                raise ValueError("Numeric comparison requires min_value.")

            try:
                number = Decimal(str(value))
            except (InvalidOperation, ValueError):
                raise ValueError("Numeric value must be valid.")

            if not number.is_finite():
                raise ValueError("Numeric value must be finite.")

            if number < 0:
                raise ValueError("Numeric value cannot be negative.")

        elif operator == "between":
            minimum = condition.get("min_value")
            maximum = condition.get("max_value")

            if minimum is None or maximum is None:
                raise ValueError(
                    "Between operator requires min_value and max_value."
                )

            try:
                minimum = Decimal(str(minimum))
                maximum = Decimal(str(maximum))
            except (InvalidOperation, ValueError):
                raise ValueError("Range values must be valid numbers.")

            if not minimum.is_finite() or not maximum.is_finite():
                raise ValueError("Range values must be finite.")

            if minimum < 0 or maximum < 0:
                raise ValueError("Range values cannot be negative.")

            if minimum > maximum:
                raise ValueError(
                    "Minimum value cannot exceed maximum value."
                )

        else:
            value = condition.get("min_value")

            if value is None:
                raise ValueError(
                    "Numeric comparison requires min_value."
                )

            try:
                number = Decimal(str(value))
            except (InvalidOperation, ValueError):
                raise ValueError("Numeric value must be valid.")

            if not number.is_finite():
                raise ValueError("Numeric value must be finite.")

            if number < 0:
                raise ValueError("Numeric value cannot be negative.")

    elif field_name in TEXT_FIELDS:
        if operator not in {"equals", "not_equals"}:
            raise ValueError(
                "Text fields support only equals and not_equals."
            )

        value = condition.get("value_text")

        if not isinstance(value, str) or not value.strip():
            raise ValueError("Text comparison requires a non-empty value_text.")

    return True


NUMERIC_FIELDS = {"age", "annual_income"}


def evaluate_condition(condition, profile):
    """
    Returns:
        True  -> Condition passed
        False -> Condition failed
        None  -> Missing or invalid information
    """

    field = condition["field_name"]
    operator = condition["operator"]

    if field not in profile or profile[field] is None:
        return None

    user_value = profile[field]

    if isinstance(user_value, str) and not user_value.strip():
        return None

    # Numeric comparisons
    if field in NUMERIC_FIELDS:
        try:
            user_value = float(user_value)
        except (TypeError, ValueError):
            return None

        if operator == "less_than":
            return user_value < float(condition["max_value"])

        elif operator == "less_than_or_equal":
            return user_value <= float(condition["max_value"])

        elif operator == "greater_than":
            return user_value > float(condition["min_value"])

        elif operator == "greater_than_or_equal":
            return user_value >= float(condition["min_value"])

        elif operator == "between":
            return (
                float(condition["min_value"])
                <= user_value
                <= float(condition["max_value"])
            )

    # Text comparisons
    else:
        expected_value = condition["value_text"]

        if expected_value is None:
            return None

        user_value = str(user_value).strip().lower()
        expected_value = str(expected_value).strip().lower()

        if operator == "equals":
            return user_value == expected_value

        elif operator == "not_equals":
            return user_value != expected_value

    raise ValueError(f"Unsupported operator: {operator}")


def match_scheme_eligibility(conditions, profile):
    """
    Compares a user's profile against scheme conditions.
    """

    if not conditions:
        return {
            "status": "needs_verification",
            "reason": "No eligibility conditions available."
        }

    mandatory_conditions = [
        condition for condition in conditions
        if condition["is_mandatory"]
    ]

    if not mandatory_conditions:
        return {
            "status": "needs_verification",
            "reason": "No mandatory eligibility conditions available."
        }

    failed_conditions = []
    unknown_conditions = []

    for condition in mandatory_conditions:

        if condition["verification_status"] != "verified":
            unknown_conditions.append(condition)
            continue

        result = evaluate_condition(condition, profile)

        if result is False:
            failed_conditions.append(condition)

        elif result is None:
            unknown_conditions.append(condition)

    # A verified mandatory failure is decisive.
    if failed_conditions:
        return {
            "status": "not_eligible",
            "reason": "At least one verified mandatory condition failed.",
            "failed_conditions": failed_conditions,
            "unknown_conditions": unknown_conditions
        }

    if unknown_conditions:
        return {
            "status": "needs_verification",
            "reason": "Some conditions are missing or pending verification.",
            "unknown_conditions": unknown_conditions
        }

    return {
        "status": "potentially_eligible",
        "reason": "All verified mandatory conditions passed."
    }
