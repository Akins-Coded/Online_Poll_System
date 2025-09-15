from django.core.cache import cache
from .models import Vote


VOTE_CACHE_TIMEOUT = 60 * 5  # cache for 5 minutes


def get_user_vote(user_id: int, poll_id: int):
    """
    Retrieve cached vote if available, otherwise fetch from DB and cache it.
    """
    cache_key = f"user_vote:{user_id}:{poll_id}"
    vote = cache.get(cache_key)

    if vote is None:
        try:
            vote = Vote.objects.get(user_id=user_id, poll_id=poll_id)
            cache.set(cache_key, vote, VOTE_CACHE_TIMEOUT)
        except Vote.DoesNotExist:
            return None
    return vote


def set_user_vote(vote: Vote):
    """
    Store user vote in cache after saving to DB.
    """
    cache_key = f"user_vote:{vote.user_id}:{vote.poll_id}"
    cache.set(cache_key, vote, VOTE_CACHE_TIMEOUT)


def clear_user_vote_cache(user_id: int, poll_id: int):
    """
    Clear vote cache for a user-poll pair.
    """
    cache_key = f"user_vote:{user_id}:{poll_id}"
    cache.delete(cache_key)
