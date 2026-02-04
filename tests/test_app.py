import pytest
from fastapi.testclient import TestClient


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_returns_correct_structure(self, client):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        data = response.json()

        for activity_name, activity in data.items():
            assert isinstance(activity_name, str)
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)

    def test_get_activities_returns_expected_activities(self, client):
        """Test that expected activities are returned."""
        response = client.get("/activities")
        data = response.json()
        activity_names = list(data.keys())

        assert "Basketball Team" in activity_names
        assert "Soccer Club" in activity_names
        assert "Art Club" in activity_names
        assert "Drama Club" in activity_names
        assert "Debate Team" in activity_names
        assert "Science Club" in activity_names
        assert "Chess Club" in activity_names
        assert "Programming Class" in activity_names
        assert "Gym Class" in activity_names


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant(self, client):
        """Test signing up a new participant to an activity."""
        response = client.post("/activities/Basketball Team/signup?email=newstudent@school.com")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Verify the signup actually happened by checking the activities endpoint
        activities = client.get("/activities").json()
        assert "newstudent@school.com" in activities["Basketball Team"]["participants"]

    def test_signup_already_registered(self, client):
        """Test that signup fails if student is already registered."""
        email = "newstudent2@school.com"
        # First signup
        client.post(f"/activities/Basketball Team/signup?email={email}")
        # Second signup should fail
        response = client.post(f"/activities/Basketball Team/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test that signup fails for non-existent activity."""
        response = client.post("/activities/Nonexistent Club/signup?email=student@school.com")
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_with_valid_email(self, client):
        """Test signup with various valid email formats."""
        emails = [
            "student@school.com",
            "john.doe@school.com",
            "jane_smith@school.com"
        ]

        for email in emails:
            response = client.post(f"/activities/Art Club/signup?email={email}")
            assert response.status_code == 200
            # Verify by checking activities endpoint
            activities = client.get("/activities").json()
            assert email in activities["Art Club"]["participants"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_existing_participant(self, client):
        """Test unregistering a participant from an activity."""
        email = "unreg_student@school.com"
        # First signup
        client.post(f"/activities/Drama Club/signup?email={email}")
        # Then unregister
        response = client.delete(f"/activities/Drama Club/unregister?email={email}")
        assert response.status_code == 200
        assert "message" in response.json()
        # Verify by checking activities endpoint
        activities = client.get("/activities").json()
        assert email not in activities["Drama Club"]["participants"]

    def test_unregister_not_registered(self, client):
        """Test that unregister fails if student is not registered."""
        response = client.delete("/activities/Science Club/unregister?email=notregistered@school.com")
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test that unregister fails for non-existent activity."""
        response = client.delete("/activities/Fake Club/unregister?email=student@school.com")
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_from_activity_with_participants(self, client):
        """Test unregistering from an activity that has pre-loaded participants."""
        # Chess Club has pre-loaded participants
        response = client.get("/activities")
        activities = response.json()
        original_participant = activities["Chess Club"]["participants"][0]

        unregister_response = client.delete(f"/activities/Chess Club/unregister?email={original_participant}")
        assert unregister_response.status_code == 200
        # Verify by checking activities endpoint
        activities = client.get("/activities").json()
        assert original_participant not in activities["Chess Club"]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static files."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests for multiple operations."""

    def test_signup_and_unregister_flow(self, client):
        """Test complete signup and unregister flow."""
        email = "integration_test@school.com"
        activity_name = "Debate Team"

        # Signup
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200

        # Verify in activities list
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]

        # Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert unregister_response.status_code == 200

        # Verify removed from activities list
        activities = client.get("/activities").json()
        assert email not in activities[activity_name]["participants"]

    def test_multiple_signups_same_activity(self, client):
        """Test multiple different students signing up for same activity."""
        activity_name = "Programming Class"
        emails = ["student1@school.com", "student2@school.com", "student3@school.com"]

        for email in emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200

        # Verify all are registered
        activities = client.get("/activities").json()
        for email in emails:
            assert email in activities[activity_name]["participants"]
