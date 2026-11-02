
import requests

BASE_URL = "http://127.0.0.1:5000/api/search"


def test_search():

    response = requests.get(
        BASE_URL,
        params={"q": "scholarships for students"}
    )

    print("Status:", response.status_code)
    print("Response:", response.json())

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "results" in data
    assert isinstance(data["results"], list)


def test_empty_query():

    response = requests.get(BASE_URL)

    assert response.status_code == 400

    print("Empty query validation passed.")


def test_long_query():

    response = requests.get(
        BASE_URL,
        params={"q": "a" * 501}
    )

    assert response.status_code == 400

    print("Long query validation passed.")


if __name__ == "__main__":

    test_search()
    test_empty_query()
    test_long_query()

    print("\nAll API tests passed!")
