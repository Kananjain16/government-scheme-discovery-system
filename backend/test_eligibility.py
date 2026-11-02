
from backend.eligibility.eligibility_rules import (
    validate_eligibility_condition
)

tests = [
    # 1. Valid text condition
    ("Valid occupation",
     {"field_name": "occupation", "operator": "equals",
      "value_text": "student"}, True),

    # 2. Valid numeric range
    ("Valid age range",
     {"field_name": "age", "operator": "between",
      "min_value": 18, "max_value": 30}, True),

    # 3. Valid numeric less_than
    ("Valid income less_than",
     {"field_name": "annual_income", "operator": "less_than",
      "min_value": 250000}, True),

    # 4. Valid numeric greater_than
    ("Valid age greater_than",
     {"field_name": "age", "operator": "greater_than",
      "min_value": 18}, True),

    # 5. Valid numeric equals
    ("Valid age equals",
     {"field_name": "age", "operator": "equals",
      "min_value": 25}, True),

    # 6. Valid text not_equals
    ("Valid category not_equals",
     {"field_name": "category", "operator": "not_equals",
      "value_text": "General"}, True),

    # 7. Invalid field
    ("Invalid field",
     {"field_name": "height", "operator": "equals",
      "value_text": "170"}, False),

    # 8. Invalid operator
    ("Invalid operator",
     {"field_name": "age", "operator": "contains",
      "min_value": 18}, False),

    # 9. Missing minimum value
    ("Missing numeric value",
     {"field_name": "age", "operator": "greater_than"}, False),

    # 10. Missing maximum value
    ("Missing range maximum",
     {"field_name": "age", "operator": "between",
      "min_value": 18}, False),

    # 11. Reversed range
    ("Reversed age range",
     {"field_name": "age", "operator": "between",
      "min_value": 30, "max_value": 18}, False),

    # 12. Negative age
    ("Negative age",
     {"field_name": "age", "operator": "greater_than",
      "min_value": -5}, False),

    # 13. Invalid numeric value
    ("Invalid income value",
     {"field_name": "annual_income", "operator": "less_than",
      "min_value": "abc"}, False),

    # 14. Text field with numeric operator
    ("Text field with numeric operator",
     {"field_name": "occupation", "operator": "greater_than",
      "min_value": 18}, False),

    # 15. Empty text value
    ("Empty text value",
     {"field_name": "state", "operator": "equals",
      "value_text": ""}, False),
]

passed = 0
failed = 0

for name, condition, expected in tests:
    try:
        validate_eligibility_condition(condition)
        actual = True
    except ValueError:
        actual = False

    if actual == expected:
        print(f"PASS: {name}")
        passed += 1
    else:
        print(f"FAIL: {name} | Expected: {expected}, Got: {actual}")
        failed += 1

print("\n----- TEST SUMMARY -----")
print(f"Total tests: {len(tests)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
