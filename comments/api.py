from django.shortcuts import get_object_or_404
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth
from better_profanity import profanity

from comments.models import Comment
from comments.schemas import (
    CommentSchema,
    CommentCreationSchema
)
from users.schemas import Error


@api_controller
class CommentController:
    @route.get("/{post_id}/comments/", response=list[CommentSchema])
    def get_comments_to_post(self, post_id: int):
        return Comment.objects.filter(post_id=post_id, is_blocked=False)

    @route.post(
        "/{post_id}/comments/",
        response={200: CommentSchema, 400: Error},
        auth=JWTAuth()
    )
    def create_comment(self, request, post_id: int, comment: CommentCreationSchema):
        comment_data = comment.model_dump()
        user_id = request.user.id

        comment_model = Comment.objects.create(
            **comment_data, user_id=user_id, post_id=post_id
        )

        if profanity.contains_profanity(comment_data["comment"]):
            comment_model.is_blocked = True
            comment_model.save()
            return 400, {"message": "Comment contains profanity"}

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
        auth=JWTAuth()
    )
    def delete_comment(self, request, comment_id: int):
        comment = get_object_or_404(Comment, id=comment_id)

        if comment.user.id != request.user.id and not request.user.is_staff:
            return 401, {"message": "Comment can be deleted only by author or admin"}

        comment.delete()
        return 200
