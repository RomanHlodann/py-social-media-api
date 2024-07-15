from typing import Optional
from ninja import Schema, ModelSchema

from comments.models import Comment


class CommentSchema(ModelSchema):
    class Meta:
        model = Comment
        fields = ("id", "post", "comment", "user", "created_at",)


class CommentCreationSchema(ModelSchema):
    class Meta:
        model = Comment
        fields = ("comment",)
