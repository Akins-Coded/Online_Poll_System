from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from datetime import timedelta


def default_created_at():
    return timezone.now()


class Poll(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="polls"
    )
    created_at = models.DateTimeField(default=default_created_at)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            if not self.created_at:
                self.created_at = default_created_at()
            self.expires_at = self.created_at + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_active(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return self.title


class Option(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)

    @property
    def votes_count(self):
        """Returns number of votes for this option."""
        return self.votes.count()

    def __str__(self):
        return f"{self.poll.title} — {self.text}"


class Vote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes"
    )
    poll = models.ForeignKey("Poll", on_delete=models.CASCADE, related_name="votes")
    option = models.ForeignKey("Option", on_delete=models.CASCADE, related_name="votes")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "poll"], name="unique_user_poll_vote")
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.option.text}"

    @staticmethod
    def get_user_vote(user_id, poll_id):
        cache_key = f"user_vote:{user_id}:{poll_id}"
        vote_id = cache.get(cache_key)
        if vote_id is not None:
            return Vote.objects.filter(id=vote_id).first()

        vote = Vote.objects.filter(user_id=user_id, poll_id=poll_id).first()
        if vote:
            cache.set(cache_key, vote.id, timeout=60 * 5)
        return vote

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # update user_vote cache
        cache.set(f"user_vote:{self.user_id}:{self.poll_id}", self.id, timeout=60 * 5)

        # invalidate poll results cache
        cache.delete(f"poll_results:{self.poll_id}")

    def delete(self, *args, **kwargs):
        # invalidate user_vote cache
        cache.delete(f"user_vote:{self.user_id}:{self.poll_id}")

        # invalidate poll results cache
        cache.delete(f"poll_results:{self.poll_id}")

        super().delete(*args, **kwargs)
