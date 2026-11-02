
import requests

BASE_URL = "http://127.0.0.1:5000/api/eligibility/check"


def test_valid_profile():

    payload = {
        "scheme_id": 11,
        "profile": {
            "age": 22,
            "annual_income": 200000,
            "state": "Uttar Pradesh",
            "occupation": "student",
            "gender": "female",
            "category": "OBC"
        }
    }

    response = requests.post(
        BASE_URL,
        json=payload
    )

    print("\nValid profile test")
    print("Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "result" in data

    assert data["result"]["status"] in (
        "potentially_eligible",
        "not_eligible",
        "needs_verification"
    )


def test_missing_profile():

    payload = {
        "scheme_id": 11,
        "profile": {}
    }

    response = requests.post(
        BASE_URL,
        json=payload
    )

    print("\nMissing profile test")
    print("Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 200

    assert (
        response.json()["result"]["status"]
        == "needs_verification"
    )


def test_invalid_scheme():

    payload = {
        "scheme_id": 999999999,
        "profile": {
            "age": 22
        }
    }

    response = requests.post(
        BASE_URL,
        json=payload
    )

    print("\nInvalid scheme test")
    print("Status:", response.status_code)

    assert response.status_code == 404


def test_invalid_age():

    payload = {
        "scheme_id": 11,
        "profile": {
            "age": -5
        }
    }

    response = requests.post(
        BASE_URL,
        json=payload
    )

    print("\nInvalid age test")
    print("Status:", response.status_code)

    assert response.status_code == 400


def test_invalid_profile_field():

    payload = {
        "scheme_id": 11,
        "profile": {
            "age": 22,
            "random_field": "test"
        }
    }

    response = requests.post(
        BASE_URL,
        json=payload
    )

    print("\nInvalid field test")
    print("Status:", response.status_code)

    assert response.status_code == 400


if __name__ == "__main__":

    test_valid_profile()
    test_missing_profile()
    test_invalid_scheme()
    test_invalid_age()
    test_invalid_profile_field()

    print("\nAll API tests passed.")
