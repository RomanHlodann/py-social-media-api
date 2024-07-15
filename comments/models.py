from django.db import models
from django.contrib.auth import get_user_model

from posts.models import Post


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments"
    )
    comment = models.TextField()
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Comment by {self.user.username}"
