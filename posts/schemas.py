from typing import Optional
from ninja import Schema, ModelSchema

from posts.models import Post


class PostSchema(ModelSchema):
    class Meta:
        model = Post
        fields = ("id", "title", "content", "user", "created_at",)


class PostCreationSchema(ModelSchema):
    class Meta:
        model = Post
        fields = ("title", "content")


class PostUpdateSchema(Schema):
    title: Optional[str] = None
    content: Optional[str] = None
