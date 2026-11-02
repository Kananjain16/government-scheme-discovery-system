
import requests

URL = "http://127.0.0.1:5000/api/discover"
TIMEOUT = 30


def send_request(payload):
    """Send POST request and safely handle the response."""

    try:
        response = requests.post(
            URL,
            json=payload,
            timeout=TIMEOUT
        )

        print("Status:", response.status_code)

        try:
            data = response.json()
            print("Response:", data)
            return response, data

        except requests.exceptions.JSONDecodeError:
            print("Response is not valid JSON:")
            print(response.text[:3000])
            return response, None

    except requests.exceptions.RequestException as e:
        print("Request failed:", str(e))
        raise


def test_tfidf_discovery():

    payload = {
        "query": "financial assistance for students",
        "method": "tfidf",
        "top_k": 10,
        "profile": {
            "age": 22,
            "annual_income": 200000,
            "state": "Uttar Pradesh",
            "occupation": "student",
            "gender": "female",
            "category": "OBC"
        }
    }

    print("\n========== TF-IDF DISCOVERY ==========")

    response, data = send_request(payload)

    assert response.status_code == 200, (
        f"TF-IDF API failed. Status: {response.status_code}"
    )

    assert data is not None, "Invalid JSON response"

    assert data["success"] is True

    result = data["data"]

    assert result["retrieval_method"] == "tfidf"
    assert "summary" in result
    assert "results" in result

    assert result["total_retrieved"] == sum(
        result["summary"].values()
    )

    print("TF-IDF discovery test passed.")


def test_semantic_discovery():

    payload = {
        "query": "money for college education",
        "method": "semantic",
        "top_k": 10,
        "profile": {
            "age": 22,
            "annual_income": 200000,
            "state": "Uttar Pradesh",
            "occupation": "student"
        }
    }

    print("\n========== SEMANTIC DISCOVERY ==========")

    response, data = send_request(payload)

    assert response.status_code == 200, (
        f"Semantic API failed. Status: {response.status_code}"
    )

    assert data is not None, "Invalid JSON response"

    assert data["success"] is True
    assert data["data"]["retrieval_method"] == "semantic"

    print("Semantic discovery test passed.")


def test_missing_query():

    payload = {
        "method": "tfidf",
        "profile": {}
    }

    print("\n========== MISSING QUERY TEST ==========")

    response, data = send_request(payload)

    assert response.status_code == 400, (
        f"Expected 400, got {response.status_code}"
    )

    print("Missing query test passed.")


def test_invalid_method():

    payload = {
        "query": "student scholarships",
        "method": "unknown",
        "profile": {}
    }

    print("\n========== INVALID METHOD TEST ==========")

    response, data = send_request(payload)

    assert response.status_code == 400, (
        f"Expected 400, got {response.status_code}"
    )

    print("Invalid method test passed.")


def test_invalid_top_k():

    payload = {
        "query": "student scholarships",
        "method": "tfidf",
        "top_k": 100,
        "profile": {}
    }

    print("\n========== INVALID TOP_K TEST ==========")

    response, data = send_request(payload)

    assert response.status_code == 400, (
        f"Expected 400, got {response.status_code}"
    )

    print("Invalid top_k test passed.")


if __name__ == "__main__":

    try:
        test_tfidf_discovery()
        test_semantic_discovery()
        test_missing_query()
        test_invalid_method()
        test_invalid_top_k()

        print("\nAll discovery API tests passed.")

    except AssertionError as e:
        print("\nTEST FAILED:", e)

    except Exception as e:
        print("\nUNEXPECTED ERROR:", e)
