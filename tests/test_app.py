from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ACTIVITY_NAME = "Chess Club"
ACTIVITY_PATH = quote(ACTIVITY_NAME, safe="")


@pytest.fixture
def api(monkeypatch):
    activities = {
        ACTIVITY_NAME: {
            "description": "Practice chess",
            "schedule": "Mondays",
            "max_participants": 2,
            "participants": ["existing@example.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)

    with TestClient(app_module.app) as client:
        yield client, activities


def test_get_activities_returns_activity_data(api):
    # Arrange
    client, activities = api

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant(api):
    # Arrange
    client, activities = api
    email = "new@example.edu"

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_PATH}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}"}
    assert activities[ACTIVITY_NAME]["participants"] == [
        "existing@example.edu",
        email,
    ]


def test_signup_rejects_duplicate_participant(api):
    # Arrange
    client, activities = api
    email = "existing@example.edu"

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_PATH}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    assert activities[ACTIVITY_NAME]["participants"] == [email]


def test_signup_rejects_unknown_activity(api):
    # Arrange
    client, activities = api
    original_participants = activities[ACTIVITY_NAME]["participants"].copy()

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup", params={"email": "new@example.edu"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities[ACTIVITY_NAME]["participants"] == original_participants


def test_remove_participant_removes_registration(api):
    # Arrange
    client, activities = api
    email = "existing@example.edu"

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_PATH}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {ACTIVITY_NAME}"}
    assert activities[ACTIVITY_NAME]["participants"] == []


def test_remove_participant_rejects_unregistered_email(api):
    # Arrange
    client, activities = api
    original_participants = activities[ACTIVITY_NAME]["participants"].copy()

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_PATH}/participants",
        params={"email": "missing@example.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activities[ACTIVITY_NAME]["participants"] == original_participants


def test_remove_participant_rejects_unknown_activity(api):
    # Arrange
    client, activities = api
    original_participants = activities[ACTIVITY_NAME]["participants"].copy()

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/participants",
        params={"email": "existing@example.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activities[ACTIVITY_NAME]["participants"] == original_participants