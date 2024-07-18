import json

from django.utils import timezone
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import RefreshToken

from posts.models import Post
from posts.tests import sample_post
from comments.models import Comment


def sample_comment(post_id, user_id):
    return {
        "post_id": post_id,
        "comment": "Comment",
        "user_id": user_id
    }


class CommentUnauthorizedTests(TestCase):
    def setUp(self):
        self.client = Client()
        user = get_user_model().objects.create_superuser(
            username="admin", password="admin"
        )
        post_data = sample_post()
        post1 = Post(**post_data)
        post1.save()

        post_data["title"] = "Another post"
        post2 = Post(**post_data)
        post2.save()

        first_comment = Comment.objects.create(**sample_comment(post1.id, user.id))
        first_comment.save()

        second_comment = Comment.objects.create(**sample_comment(post2.id, user.id))
        second_comment.save()

    def test_unauthorized_request_to_modify_comment_or_get_analytics(self):
        res1 = self.client.post("/api/posts/1/comments/", {})
        res2 = self.client.patch("/api/posts/1/comments/1/", {})
        res3 = self.client.delete("/api/posts/1/comments/1/", {})
        res4 = self.client.get("/api/posts/comments-daily-breakdown/")

        self.assertEqual(res1.status_code, 401)
        self.assertEqual(res2.status_code, 401)
        self.assertEqual(res3.status_code, 401)
        self.assertEqual(res4.status_code, 401)

    def test_request_to_get_comments_to_post(self):
        response = self.client.get("/api/posts/1/comments/")
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_data), 1)


class CommentUserAuthorizedTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="user1", password="user1"
        )
        self.other_user = get_user_model().objects.create_user(
            username="user2", password="user2"
        )
        self.post = Post(**sample_post(), auto_reply_enabled=True)
        self.post.save()

        self.headers = {
            "HTTP_AUTHORIZATION": f"Bearer {str(RefreshToken.for_user(self.user).access_token)}"
        }
        self.headers2 = {
            "HTTP_AUTHORIZATION": f"Bearer {str(RefreshToken.for_user(self.other_user).access_token)}"
        }
        Comment.objects.create(**sample_comment(self.post.id, self.other_user.id))

    def test_get_analytics(self):
        response = self.client.get(
            "/api/posts/comments-daily-breakdown/?date_from=2023-01-01&date_to=2023-01-31",
            **self.headers2
        )

        self.assertEqual(response.status_code, 403)

    def test_comment_create(self):
        comment_data = sample_comment(self.post.id, self.other_user.id)
        comment_data["comment"] = "Another comment"

        response = self.client.post(
            "/api/posts/1/comments/",
            data=json.dumps(comment_data),
            content_type="application/json",
            **self.headers2
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Comment.objects.get(comment="Another comment"))

    def test_comment_create_with_profanity(self):
        comment_data = sample_comment(self.post.id, self.other_user.id)
        comment_data["comment"] = "damn"

        response = self.client.post(
            "/api/posts/1/comments/",
            data=json.dumps(comment_data),
            content_type="application/json",
            **self.headers2
        )

        self.assertEqual(response.status_code, 400)

    def test_comment_create_to_non_existing_post(self):
        comment_data = sample_comment(self.post.id, self.user.id)
        comment_data["comment"] = "Another comment"

        response = self.client.post(
            "/api/posts/2/comments/",
            data=json.dumps(comment_data),
            content_type="application/json",
            **self.headers
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            len(Comment.objects.filter(comment="Another comment")),
            0
        )

    def test_comment_update_by_owner(self):
        comment_data = {"comment": "New comment"}

        response = self.client.patch(
            "/api/posts/1/comments/1/",
            data=json.dumps(comment_data),
            content_type="application/json",
            **self.headers2
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.get(comment="New comment"))

    def test_comment_update_by_not_owner(self):
        comment_data = {"comment": "New comment"}

        response = self.client.patch(
            "/api/posts/1/comments/1/",
            data=json.dumps(comment_data),
            content_type="application/json",
            **self.headers
        )

        self.assertEqual(response.status_code, 400)

    def test_comment_update_with_profanity(self):
        comment_data = {"comment": "damn"}

        response = self.client.patch(
            "/api/posts/1/comments/1/",
            data=json.dumps(comment_data),
            content_type="application/json",
            **self.headers2
        )

        self.assertEqual(response.status_code, 400)

    def test_delete_comment(self):
        response = self.client.delete(
            "/api/posts/1/comments/1/",
            **self.headers2
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Comment.objects.all()), 0)


class CommentAdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_superuser(
            username="admin", password="admin"
        )
        self.headers = {
            "HTTP_AUTHORIZATION": f"Bearer {str(RefreshToken.for_user(self.user).access_token)}"
        }
        post_data = sample_post()
        post1 = Post(**post_data)
        post1.save()

        post_data["title"] = "Another post"
        post2 = Post(**post_data)
        post2.save()

        comment = Comment.objects.create(**sample_comment(post1.id, self.user.id))
        comment.save()

        data_with_profanity = sample_comment(post2.id, self.user.id)
        data_with_profanity["is_blocked"] = True
        comment_with_profanity = Comment.objects.create(**data_with_profanity)
        comment_with_profanity.save()

    def test_get_analytics(self):
        today = timezone.now().date()

        response = self.client.get(
            f"/api/posts/comments-daily-breakdown/?date_from={today}&date_to={today}",
            **self.headers
        )
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["results"][0]["created_count"], 2)
        self.assertEqual(response_data["results"][0]["blocked_count"], 1)

    def test_get_analytics_with_date_limiter(self):
        comment_data = sample_comment(1, self.user.id)
        comment = Comment.objects.create(**comment_data)
        comment.created_at = "2023-07-11"
        comment.save()

        response = self.client.get(
            f"/api/posts/comments-daily-breakdown/?date_from=2023-07-11&date_to=2023-07-11",
            **self.headers
        )
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["results"][0]["created_count"], 1)
        self.assertEqual(response_data["results"][0]["blocked_count"], 0)
