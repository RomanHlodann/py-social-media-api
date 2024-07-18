from django.db import models
from django.contrib.auth import get_user_model


class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_blocked = models.BooleanField(default=False)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="posts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    auto_reply_enabled = models.BooleanField(default=False)
    auto_reply_delay = models.FloatField(default=0)

    def __str__(self) -> str:
        return f"Post by {self.user.username}"
