from django.shortcuts import get_object_or_404
from ninja_extra import NinjaExtraAPI, api_controller, route
from ninja_jwt.authentication import JWTAuth
from better_profanity import profanity

from posts.models import Post
from posts.schemas import PostSchema, PostCreationSchema, PostUpdateSchema
from users.schemas import Error
from comments.api import CommentController


api = NinjaExtraAPI(urls_namespace="post-api")


@api_controller
class PostController:
    @route.get("/", response=list[PostSchema])
    def get_posts(self):
        return Post.objects.all()

    @route.post(
        "/",
        response={200: PostSchema, 401: Error, 400: Error},
        auth=JWTAuth()
    )
    def create_post(self, request, post: PostCreationSchema):
        post_data = post.model_dump()
        user_id = request.user.id

        post_model = Post.objects.create(**post_data, user_id=user_id)

        if (profanity.contains_profanity(post_data["title"])
                or profanity.contains_profanity(post_data["content"])):
            post_model.is_blocked = True
            post_model.save()
            return 400, {"message": "Post contains profanity"}

        return post_model

    @route.get("/{post_id}/", response=PostSchema)
    def get_post(self, post_id: int):
        return get_object_or_404(Post, id=post_id)

    @route.patch(
        "/{post_id}/",
        response={200: PostSchema, 401: Error, 400: Error},
        auth=JWTAuth()
    )
    def update_post(self, request, post_id: int, new_post: PostUpdateSchema):
        post = get_object_or_404(Post, id=post_id)

        if post.user.id != request.user.id and not request.user.is_staff:
            return 401, {"message": "Post can be changed only by author or admin"}

        for attr, value in new_post.model_dump().items():
            if value:
                setattr(post, attr, value)

        if (profanity.contains_profanity(new_post["title"])
                or profanity.contains_profanity(new_post["content"])):
            post.is_blocked = True
            post.save()
            return 400, {"message": "Post contains profanity"}

        post.save()
        return post

    @route.delete(
        "/{post_id}/",
        auth=JWTAuth()
    )
    def delete_post(self, request, post_id: int):
        post = get_object_or_404(Post, id=post_id)

        if post.user.id != request.user.id and not request.user.is_staff:
            return 401, {"message": "Post can be deleted only by author or admin"}

        post.delete()
        return 200


api.register_controllers(CommentController, PostController)
