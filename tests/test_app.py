from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ACTIVITY_NAME = "Chess Club"
PARTICIPANT_EMAIL = "new.student@mergington.edu"
ACTIVITY_SIGNUP_URL = f"/activities/{quote(ACTIVITY_NAME, safe='')}/signup"


@pytest.fixture
def client(monkeypatch):
    activities = {
        ACTIVITY_NAME: {
            "description": "Practice chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["existing.student@mergington.edu"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activities = {
        ACTIVITY_NAME: {
            "description": "Practice chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["existing.student@mergington.edu"],
        }
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client):
    # Arrange
    expected_message = f"Signed up {PARTICIPANT_EMAIL} for {ACTIVITY_NAME}"

    # Act
    response = client.post(ACTIVITY_SIGNUP_URL, params={"email": PARTICIPANT_EMAIL})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": expected_message}
    assert PARTICIPANT_EMAIL in activities_response.json()[ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_without_changing_participants(client):
    # Arrange
    existing_email = "existing.student@mergington.edu"

    # Act
    response = client.post(ACTIVITY_SIGNUP_URL, params={"email": existing_email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activities_response.json()[ACTIVITY_NAME]["participants"] == [existing_email]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    unknown_activity_url = f"/activities/{quote('Unknown Club', safe='')}/signup"

    # Act
    response = client.post(unknown_activity_url, params={"email": PARTICIPANT_EMAIL})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    existing_email = "existing.student@mergington.edu"

    # Act
    response = client.delete(ACTIVITY_SIGNUP_URL, params={"email": existing_email})
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {existing_email} from {ACTIVITY_NAME}"
    }
    assert activities_response.json()[ACTIVITY_NAME]["participants"] == []


def test_unregister_returns_404_for_missing_participant(client):
    # Arrange
    missing_email = "missing.student@mergington.edu"

    # Act
    response = client.delete(ACTIVITY_SIGNUP_URL, params={"email": missing_email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    unknown_activity_url = f"/activities/{quote('Unknown Club', safe='')}/signup"

    # Act
    response = client.delete(unknown_activity_url, params={"email": PARTICIPANT_EMAIL})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_then_unregister_clears_participant(client):
    # Arrange
    signup_params = {"email": PARTICIPANT_EMAIL}

    # Act
    signup_response = client.post(ACTIVITY_SIGNUP_URL, params=signup_params)
    unregister_response = client.delete(ACTIVITY_SIGNUP_URL, params=signup_params)
    activities_response = client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert unregister_response.status_code == 200
    assert activities_response.json()[ACTIVITY_NAME]["participants"] == [
        "existing.student@mergington.edu"
    ]