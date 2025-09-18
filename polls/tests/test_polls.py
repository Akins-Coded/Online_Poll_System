import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from polls.models import Poll, Option, Vote
from django.contrib.auth import get_user_model

User = get_user_model()


# -----------------------------
# Fixtures
# -----------------------------
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


@pytest.fixture
def active_poll(db, admin_user):
    poll = Poll.objects.create(
        title="Active Poll",
        description="For testing",
        created_by=admin_user,
        expires_at=timezone.now() + timedelta(days=1)
    )
    Option.objects.bulk_create([
        Option(poll=poll, text="Option 1"),
        Option(poll=poll, text="Option 2"),
    ])
    return poll


@pytest.fixture
def expired_poll(db, admin_user):
    poll = Poll.objects.create(
        title="Expired Poll",
        description="Should not accept votes",
        created_by=admin_user,
        expires_at=timezone.now() - timedelta(days=1)
    )
    Option.objects.bulk_create([
        Option(poll=poll, text="Option 1"),
        Option(poll=poll, text="Option 2"),
    ])
    return poll


# -----------------------------
# Poll Creation Tests
# -----------------------------
@pytest.mark.django_db
def test_admin_can_create_poll(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    url = reverse("poll-list")
    payload = {
        "title": "New Poll",
        "description": "Test poll",
        "options": ["Yes", "No", "Maybe"]
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert Poll.objects.filter(title="New Poll").exists()
    poll = Poll.objects.get(title="New Poll")
    assert poll.options.count() == 3


@pytest.mark.django_db
def test_non_admin_cannot_create_poll(api_client, voter_user):
    api_client.force_authenticate(user=voter_user)
    url = reverse("poll-list")
    payload = {"title": "Unauthorized Poll", "options": ["A", "B"]}
    response = api_client.post(url, payload, format="json")
    assert response.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)
    assert not Poll.objects.filter(title="Unauthorized Poll").exists()


# -----------------------------
# Voting Tests
# -----------------------------
@pytest.mark.django_db
def test_voter_can_vote(api_client, voter_user, active_poll):
    option = active_poll.options.first()
    api_client.force_authenticate(user=voter_user)
    url = reverse("poll-vote", kwargs={"pk": active_poll.id})
    response = api_client.post(url, {"option_id": option.id}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert Vote.objects.filter(user=voter_user, poll=active_poll).exists()


@pytest.mark.django_db
def test_prevent_duplicate_vote(api_client, voter_user, active_poll):
    option = active_poll.options.first()
    Vote.objects.create(user=voter_user, poll=active_poll, option=option)

    api_client.force_authenticate(user=voter_user)
    url = reverse("poll-vote", kwargs={"pk": active_poll.id})
    response = api_client.post(url, {"option_id": option.id}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already voted" in str(response.data).lower()


# -----------------------------
# Expired Poll Tests
# -----------------------------
@pytest.mark.django_db
def test_vote_on_expired_poll_blocked(api_client, voter_user, expired_poll):
    option = expired_poll.options.first()
    api_client.force_authenticate(user=voter_user)
    url = reverse("poll-vote", kwargs={"pk": expired_poll.id})
    response = api_client.post(url, {"option_id": option.id}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "expired" in str(response.data).lower()
    assert Vote.objects.filter(poll=expired_poll).count() == 0


@pytest.mark.django_db
def test_add_option_to_expired_poll_blocked(api_client, admin_user, expired_poll):
    api_client.force_authenticate(user=admin_user)
    url = reverse("poll-options", kwargs={"pk": expired_poll.id})
    response = api_client.post(url, {"text": "Extra Option"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "expired" in str(response.data).lower()
    assert expired_poll.options.count() == 2  # No new options added


@pytest.mark.django_db
def test_add_option_to_active_poll_allowed(api_client, admin_user, active_poll):
    api_client.force_authenticate(user=admin_user)
    url = reverse("poll-options", kwargs={"pk": active_poll.id})
    response = api_client.post(url, {"text": "Extra Option"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert active_poll.options.count() == 3


# -----------------------------
# Results Tests
# -----------------------------
@pytest.mark.django_db
def test_poll_results_accuracy(api_client, voter_user, active_poll):
    # Cast votes
    opts = list(active_poll.options.all())
    Vote.objects.create(user=voter_user, poll=active_poll, option=opts[0])
    Vote.objects.create(user=active_poll.created_by, poll=active_poll, option=opts[1])

    url = reverse("poll-results", kwargs={"pk": active_poll.id})
    response = api_client.get(url, format="json")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_votes"] == 2
    assert sum(opt["votes_count"] for opt in data["options"]) == 2
