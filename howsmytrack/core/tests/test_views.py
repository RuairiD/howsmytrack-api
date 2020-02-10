from django.test import Client
from django.test import TestCase


class LogoutTest(TestCase):
    """Test JWT cookie is deleted on logout."""
    def test_logout(self):
        client = Client()
        response = client.get('/logout', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies['JWT'].value, '')
