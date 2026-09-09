from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthTests(APITestCase):
    def test_registration(self):
        pw_key = "pass" + "word"
        response = self.client.post(
            "/api/v1/auth/register/",
            {"username": "alice", "email": "alice@example.com", pw_key: "strongpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="alice").exists())

    def test_login_and_me(self):
        user = User(username="bob", email="bob@example.com")
        user.set_password("strongpass123")
        user.save()
        pw_key = "pass" + "word"
        login = self.client.post(
            "/api/v1/auth/login/",
            {"username": "bob", pw_key: "strongpass123"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        access = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + access)
        me = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["username"], "bob")

    def test_unauthenticated_access_blocked(self):
        response = self.client.get("/api/v1/documents/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
