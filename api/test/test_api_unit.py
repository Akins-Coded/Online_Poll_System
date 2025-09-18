import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        password="StrongPass123",
        first_name="Admin",
        surname="User"
    )


@pytest.fixture
def voter_user(db):
    return User.objects.create_user(
        email="voter@example.com",
        password="StrongPass123",
        first_name="Voter",
        surname="User"
    )


# --- Register View Tests ---
@pytest.mark.django_db
def test_register_voter(api_client):
    url = reverse("auth_register")
    payload = {
        "first_name": "John",
        "surname": "Doe",
        "email": "john@example.com",
        "confirm_email": "john@example.com",
        "password": "MySecret123",
        "confirm_password": "MySecret123",
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    user = User.objects.get(email="john@example.com")
    assert user.role == User.Roles.VOTER
    assert user.check_password("MySecret123")


@pytest.mark.django_db
def test_register_password_mismatch(api_client):
    url = reverse("auth_register")
    payload = {
        "first_name": "Jane",
        "surname": "Doe",
        "email": "jane@example.com",
        "confirm_email": "jane@example.com",
        "password": "Pass1234",
        "confirm_password": "Pass12345",
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data
    assert response.data["password"][0] == "Passwords do not match."


@pytest.mark.django_db
def test_register_email_mismatch(api_client):
    url = reverse("auth_register")
    payload = {
        "first_name": "Jane",
        "surname": "Doe",
        "email": "jane@example.com",
        "confirm_email": "jane2@example.com",
        "password": "Pass1234",
        "confirm_password": "Pass1234",
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data
    assert response.data["email"][0] == "Emails do not match."


# --- Login View Tests ---
@pytest.mark.django_db
def test_login_user(api_client, voter_user):
    url = reverse("auth_login")
    payload = {"email": "voter@example.com", "password": "StrongPass123"}
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


# --- UserViewSet Tests (Admin Operations) ---
@pytest.mark.django_db
def test_admin_create_admin(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    url = reverse("user-create-admin")
    payload = {
        "email": "newadmin@example.com",
        "password": "AdminPass123",
        "first_name": "New",
        "surname": "Admin",
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    user = User.objects.get(email="newadmin@example.com")
    assert user.role == User.Roles.ADMIN
    assert user.is_staff
    assert user.is_superuser


@pytest.mark.django_db
def test_non_admin_cannot_create_admin(api_client, voter_user):
    api_client.force_authenticate(user=voter_user)
    url = reverse("user-create-admin")
    payload = {
        "email": "hackadmin@example.com",
        "password": "HackPass123",
        "first_name": "Hack",
        "surname": "User",
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


# --- UserListView Tests ---
@pytest.mark.django_db
def test_admin_can_list_users(api_client, admin_user, voter_user):
    api_client.force_authenticate(user=admin_user)
    url = reverse("user_list")
    response = api_client.get(url, format="json")
    
    # Assertions
    assert response.status_code == status.HTTP_200_OK
    
    # Check if the response data has the expected pagination structure
    assert "results" in response.data
    
    # Assert the number of users in the 'results' list
    assert len(response.data["results"]) == 2 # This is the key change
    
    # Optional: Check the count key
    assert response.data["count"] == 2


@pytest.mark.django_db
def test_voter_cannot_list_users(api_client, voter_user):
    api_client.force_authenticate(user=voter_user)
    url = reverse("user_list")
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_unauthenticated_cannot_list_users(api_client):
    url = reverse("user_list")
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
