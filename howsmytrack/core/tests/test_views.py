from django.test import Client
from django.test import TestCase


class LogoutTest(TestCase):
    """Test JWT cookie is deleted on logout."""

    def test_logout(self):
        client = Client()
        response = client.get("/logout", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies["JWT"].value, "")


class RedirectToWwwTest(TestCase):
    """Test index page redirects to www homepage."""

    def test_redirect_to_www(self):
        client = Client()
        response = client.get("", follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://www.howsmytrack.com/")
