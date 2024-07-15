from django.db import models
from django.contrib.auth import get_user_model


class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="posts"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Created at {self.created_at} by {self.user.username}"
