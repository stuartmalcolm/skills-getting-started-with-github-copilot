from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_root_redirects_to_frontend(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert activity_name in response.json()
    assert isinstance(response.json()[activity_name]["participants"], list)


def test_signup_adds_participant_to_encoded_activity_name(client):
    # Arrange
    activity_name = "Programming Class"
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        "/activities/Programming%20Class/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant_without_mutation(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    participants_before = list(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities[activity_name]["participants"] == participants_before


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


@pytest.mark.parametrize(
    ("spots_from_capacity", "expected_status"),
    [(-1, 200), (0, 409), (1, 409)],
    ids=["last-available-spot", "at-capacity", "over-capacity"],
)
def test_signup_enforces_participant_capacity(
    client, spots_from_capacity, expected_status
):
    # Arrange
    activity_name = "Programming Class"
    activity = activities[activity_name]
    occupied_spots = activity["max_participants"] + spots_from_capacity
    activity["participants"] = [
        f"student-{index}@mergington.edu" for index in range(occupied_spots)
    ]
    participants_before = list(activity["participants"])
    email = "last-student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == expected_status
    if expected_status == 200:
        assert len(activity["participants"]) == activity["max_participants"]
        assert email in activity["participants"]
    else:
        assert response.json()["detail"] == "Activity is full"
        assert activity["participants"] == participants_before


@pytest.mark.parametrize(
    ("method", "email"),
    [
        ("post", None),
        ("delete", None),
        ("post", ""),
        ("delete", ""),
        ("post", "not-an-email"),
        ("delete", "not-an-email"),
    ],
    ids=[
        "signup-missing-email",
        "unregister-missing-email",
        "signup-blank-email",
        "unregister-blank-email",
        "signup-malformed-email",
        "unregister-malformed-email",
    ],
)
def test_mutation_routes_require_valid_email(client, method, email):
    # Arrange
    activity_name = "Chess Club"
    participants_before = list(activities[activity_name]["participants"])
    params = {} if email is None else {"email": email}
    request = getattr(client, method)

    # Act
    response = request(f"/activities/{activity_name}/signup", params=params)

    # Assert
    assert response.status_code == 422
    assert activities[activity_name]["participants"] == participants_before


def test_unregister_removes_participant_and_rejects_repeat_request(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    url = f"/activities/{activity_name}/signup"

    # Act
    response = client.delete(url, params={"email": email})
    repeated_response = client.delete(url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert repeated_response.status_code == 404
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_participant_not_in_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "absent-student@mergington.edu"
    participants_before = list(activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities[activity_name]["participants"] == participants_before


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"