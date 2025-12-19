"""
FastAPI tests for the Mergington High School Activities app
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from fastapi.testclient import TestClient
from app import app, activities

# Create a test client
client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_dict(self):
        """Test that /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that /activities contains expected activities"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = ["Soccer", "Basketball", "Debate Club", "Math Olympiad", 
                              "Drama Club", "Art Studio", "Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant(self):
        """Test signing up a new participant"""
        response = client.post("/activities/Soccer/signup?email=test@mergington.edu")
        assert response.status_code == 200
        assert "test@mergington.edu" in activities["Soccer"]["participants"]

    def test_signup_returns_success_message(self):
        """Test that signup returns a success message"""
        response = client.post("/activities/Basketball/signup?email=newuser@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "signed up" in data["message"].lower() or "signup" in data["message"].lower()

    def test_signup_duplicate_participant_fails(self):
        """Test that signing up the same person twice fails"""
        email = "duplicate@mergington.edu"
        # First signup should succeed
        response1 = client.post(f"/activities/Soccer/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Soccer/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_nonexistent_activity_fails(self):
        """Test that signing up for a non-existent activity fails"""
        response = client.post("/activities/NonexistentActivity/signup?email=test@mergington.edu")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_participant(self):
        """Test unregistering a participant"""
        email = "unregister@mergington.edu"
        # First signup
        client.post(f"/activities/Drama Club/signup?email={email}")
        assert email in activities["Drama Club"]["participants"]
        
        # Then unregister
        response = client.post(f"/activities/Drama Club/unregister?email={email}")
        assert response.status_code == 200
        assert email not in activities["Drama Club"]["participants"]

    def test_unregister_returns_success_message(self):
        """Test that unregister returns a success message"""
        email = "unregister2@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        response = client.post(f"/activities/Chess Club/unregister?email={email}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "unregistered" in data["message"].lower()

    def test_unregister_nonexistent_activity_fails(self):
        """Test that unregistering from a non-existent activity fails"""
        response = client.post("/activities/NonexistentActivity/unregister?email=test@mergington.edu")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_nonparticipant_fails(self):
        """Test that unregistering someone not registered fails"""
        email = "notregistered@mergington.edu"
        response = client.post(f"/activities/Art Studio/unregister?email={email}")
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()


class TestRootEndpoint:
    """Tests for the / endpoint"""

    def test_root_redirects_to_static(self):
        """Test that / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200


class TestIntegration:
    """Integration tests for signup and unregister workflows"""

    def test_signup_and_unregister_workflow(self):
        """Test a complete signup and unregister workflow"""
        activity = "Programming Class"
        email = "workflow@mergington.edu"
        
        # Initially, user is not registered
        assert email not in activities[activity]["participants"]
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        assert email not in activities[activity]["participants"]

    def test_participant_count_updates(self):
        """Test that participant count updates correctly"""
        activity = "Gym Class"
        email = "count@mergington.edu"
        
        initial_count = len(activities[activity]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        assert len(activities[activity]["participants"]) == initial_count + 1
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        assert len(activities[activity]["participants"]) == initial_count
