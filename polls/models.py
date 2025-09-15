from django.conf import settings
from django.db import models
from datetime import datetime, timedelta


def default_created_at():
    return datetime.utcnow()


class Poll(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="polls")
    created_at = models.DateTimeField(default=default_created_at)
    expires_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            if not self.created_at:
                self.created_at = default_created_at()
            self.expires_at = self.created_at + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_active(self):
        return datetime.utcnow() < self.expires_at

    def __str__(self):
        return self.title


class Option(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.poll.title} — {self.text}"


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes")
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name="votes")
    timestamp = models.DateTimeField(default=default_created_at)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "poll"], name="unique_user_poll_vote")
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.option.text}"
