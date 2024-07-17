from django.db.models import Count
from django.db.models.functions.datetime import TruncDay
from django.shortcuts import get_object_or_404
from django.db import models
from ninja_extra import api_controller, route, permissions
from ninja_jwt.authentication import JWTAuth
from ninja import Query
from better_profanity import profanity
from datetime import date

from comments.models import Comment
from comments.schemas import (
    CommentSchema,
    CommentCreationSchema
)
from posts.tasks import send_auto_reply
from posts.models import Post
from users.schemas import Error


@api_controller
class CommentController:
    @route.get(
        "/comments-daily-breakdown/",
        auth=JWTAuth(),
        permissions=[permissions.IsAdminUser],
        response=dict
    )
    def get_analytics(
            self,
            request,
            date_from: date = Query(...),
            date_to: date = Query(date.today())
    ):
        queryset = Comment.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).annotate(day=TruncDay("created_at")).values("day").annotate(
            created_count=Count("id"),
            blocked_count=Count("id", filter=models.Q(is_blocked=True))
        ).values("day", "created_count", "blocked_count")

        results = list(queryset)
        return {"results": results}

    @route.get("/{post_id}/comments/", response=list[CommentSchema])
    def get_comments_to_post(self, post_id: int):
        return Comment.objects.filter(post_id=post_id, is_blocked=False)

    @staticmethod
    def create_task_to_reply(
            user_id: int,
            post: Post,
            comment: str
    ):
        if post.user.id == user_id or not post.auto_reply_enabled:
            return
        send_auto_reply.apply_async(
            args=[post.id, post.user.id, comment],
            countdown=post.auto_reply_delay * 60
        )

    @route.post(
        "/{post_id}/comments/",
        response={200: CommentSchema, 400: Error},
        auth=JWTAuth()
    )
    def create_comment(self, request, post_id: int, comment: CommentCreationSchema):
        post = get_object_or_404(Post, id=post_id)

        comment_data = comment.model_dump()
        user_id = request.user.id

        comment_model = Comment.objects.create(
            **comment_data, user_id=user_id, post_id=post_id
        )

        if profanity.contains_profanity(comment_data["comment"]):
            comment_model.is_blocked = True
            comment_model.save()
            return 400, {"message": "Comment contains profanity"}

        self.create_task_to_reply(request.user.id, post, comment_model.comment)

        return comment_model

    @route.patch(
        "/{post_id}/comments/{comment_id}/",
        response={200: CommentSchema, 401: Error, 400: Error},
        auth=JWTAuth()
    )
    def update_comment(self, request, comment_id: int, new_comment: CommentCreationSchema):
        comment = get_object_or_404(Comment, id=comment_id)

        if comment.user.id != request.user.id and not request.user.is_staff:
            return 401, {"message": "Comment can be changed only by author or admin"}

        for attr, value in new_comment.model_dump().items():
            if value:
                setattr(comment, attr, value)

        if profanity.contains_profanity(comment.comment):
            comment.is_blocked = True
            comment.save()
            return 400, {"message": "Comment contains profanity"}

        comment.save()
        return comment

    @route.delete(
        "/{post_id}/comments/{comment_id}/",
        response={200: str, 401: Error, 400: Error},
        auth=JWTAuth()
    )
    def delete_comment(self, request, comment_id: int):
        comment = get_object_or_404(Comment, id=comment_id)

        if comment.user.id != request.user.id and not request.user.is_staff:
            return 400, {"message": "Comment can be deleted only by author or admin"}

        comment.delete()
        return "Comment was deleted"
