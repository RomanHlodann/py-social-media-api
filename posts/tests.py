import json

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import RefreshToken

from posts.models import Post


def sample_post():
    return {
        "title": "Test",
        "content": "Test",
        "user_id": 1,
    }


class PostUnauthorizedTests(TestCase):
    def setUp(self):
        self.client = Client()
        get_user_model().objects.create_superuser(
            username="admin", password="admin"
        )
        post = Post(**sample_post())
        post.save()

    def test_unauthorized_request_to_modify_post(self):
        res1 = self.client.post("/api/posts/", {})
        res2 = self.client.patch("/api/posts/1/", {})
        res3 = self.client.delete("/api/posts/1/", {})

        self.assertEqual(res1.status_code, 401)
        self.assertEqual(res2.status_code, 401)
        self.assertEqual(res3.status_code, 401)

    def test_get_posts(self):
        response = self.client.get("/api/posts/")
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_data), 1)

    def test_get_single_post(self):
        response = self.client.get("/api/posts/1/")
        response_data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data["title"], "Test")
        self.assertEqual(response_data["content"], "Test")


class PostAuthorizedTests(TestCase):
    def setUp(self):
        self.client = Client()
        user = get_user_model().objects.create_user(
            username="user1", password="user1"
        )
        self.other_user = get_user_model().objects.create_user(
            username="user2", password="user2"
        )
        post = Post(**sample_post())
        post.save()

        self.headers = {
            "HTTP_AUTHORIZATION": f"Bearer {str(RefreshToken.for_user(user).access_token)}"
        }
        self.headers2 = {
            "HTTP_AUTHORIZATION": f"Bearer {str(RefreshToken.for_user(self.other_user).access_token)}"
        }

    def test_post_create(self):
        post_data = sample_post()
        post_data["title"] = "New post"

        response = self.client.post(
            "/api/posts/",
            data=json.dumps(post_data),
            content_type="application/json",
            **self.headers
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Post.objects.get(title="New post"))

    def test_post_update_by_owner(self):
        post_data = {"title": "New post"}

        response = self.client.patch(
            "/api/posts/1/",
            data=json.dumps(post_data),
            content_type="application/json",
            **self.headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Post.objects.get(title="New post"))

    def test_post_update_by_not_owner(self):
        post_data = {"title": "New post"}

        response = self.client.patch(
            "/api/posts/1/",
            data=json.dumps(post_data),
            content_type="application/json",
            **self.headers2
        )

        self.assertEqual(response.status_code, 400)

    def test_post_delete_by_owner(self):
        response = self.client.delete(
            "/api/posts/1/",
            **self.headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Post.objects.all()), 0)

    def test_post_delete_by_not_owner(self):
        response = self.client.delete(
            "/api/posts/1/",
            **self.headers2
        )

        self.assertEqual(response.status_code, 400)
