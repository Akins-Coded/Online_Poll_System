import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from polls.models import Poll, Option, Vote
from datetime import timedelta


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email="user@example.com", password="password123"
    )


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_superuser(
        email="admin@example.com", password="password123"
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


# -----------------------------
# Poll Creation
# -----------------------------
@pytest.mark.django_db
def test_create_poll_with_options(admin_client):
    payload = {
        "title": "Favorite Food",
        "description": "Pick one",
        "options": ["Rice", "Beans"]
    }
    response = admin_client.post("/api/polls/", payload, format="json")
    assert response.status_code == 201
    poll = Poll.objects.get(title="Favorite Food")
    assert poll.options.count() == 2


# -----------------------------
# Poll Expiry Rules
# -----------------------------
@pytest.mark.django_db
def test_vote_blocked_after_expiry(auth_client, admin_client):
    # Create poll with expiry in the past
    poll = Poll.objects.create(
        title="Expired Poll",
        created_by=admin_client.handler._force_user,
        expires_at=timezone.now() - timedelta(days=1)
    )
    option = Option.objects.create(poll=poll, text="Choice A")

    response = auth_client.post(f"/api/polls/{poll.id}/vote/", {"option_id": option.id})
    assert response.status_code == 400
    assert "expired" in response.json()["error"].lower()


@pytest.mark.django_db
def test_add_option_blocked_after_expiry(admin_client):
    poll = Poll.objects.create(
        title="Expired Poll",
        created_by=admin_client.handler._force_user,
        expires_at=timezone.now() - timedelta(days=1)
    )
    response = admin_client.post(f"/api/polls/{poll.id}/options/", {"text": "Late Option"})
    assert response.status_code == 400
    assert "expired" in response.json()["error"].lower()


# -----------------------------
# Voting Uniqueness
# -----------------------------
@pytest.mark.django_db
def test_user_cannot_vote_twice(auth_client, admin_client, user):
    poll = Poll.objects.create(
        title="Vote Once",
        created_by=admin_client.handler._force_user,
        expires_at=timezone.now() + timedelta(days=1)
    )
    option = Option.objects.create(poll=poll, text="Option 1")

    # First vote
    res1 = auth_client.post(f"/api/polls/{poll.id}/vote/", {"option_id": option.id})
    assert res1.status_code == 201

    # Second vote → should fail
    res2 = auth_client.post(f"/api/polls/{poll.id}/vote/", {"option_id": option.id})
    assert res2.status_code == 400
    assert "already voted" in str(res2.json()).lower()


# -----------------------------
# Results Caching
# -----------------------------
@pytest.mark.django_db
def test_results_cache_invalidation(auth_client, admin_client):
    poll = Poll.objects.create(
        title="Caching Test",
        created_by=admin_client.handler._force_user,
        expires_at=timezone.now() + timedelta(days=1)
    )
    option = Option.objects.create(poll=poll, text="Option 1")

    # First fetch → populates cache
    res1 = auth_client.get(f"/api/polls/{poll.id}/results/")
    assert res1.status_code == 200
    assert res1.json()["total_votes"] == 0

    # Vote
    auth_client.post(f"/api/polls/{poll.id}/vote/", {"option_id": option.id})

    # Fetch results again → cache should be invalidated and updated
    res2 = auth_client.get(f"/api/polls/{poll.id}/results/")
    assert res2.status_code == 200
    assert res2.json()["total_votes"] == 1
