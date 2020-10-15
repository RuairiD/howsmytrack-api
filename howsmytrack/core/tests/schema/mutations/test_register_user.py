from unittest.mock import Mock

from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.schema.mutations.register_user import INVALID_PASSWORD_MESSAGE
from howsmytrack.core.schema.mutations.register_user import RegisterUser
from howsmytrack.schema import schema


class RegisterUserTest(TestCase):
    def setUp(self):
        self.user = FeedbackGroupsUser.create(
            email="graham@brightonandhovealbion.com", password="password",
        )
        self.user.save()

    def test_no_account(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["registerUser"]
            .resolver(
                self=Mock(),
                info=info,
                email="lewis@brightonandhovealbion.com",
                password="sussexbythesea1901",
                password_repeat="sussexbythesea1901",
            )
        )

        self.assertEqual(result, RegisterUser(success=True, error=None,))

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="lewis@brightonandhovealbion.com",
            ).count(),
            1,
        )

    def test_existing_account(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["registerUser"]
            .resolver(
                self=Mock(),
                info=info,
                email="graham@brightonandhovealbion.com",
                password="sussexbythesea1901",
                password_repeat="sussexbythesea1901",
            )
        )

        self.assertEqual(
            result,
            RegisterUser(
                success=False,
                error="An account for that email address already exists.",
            ),
        )

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="graham@brightonandhovealbion.com",
            ).count(),
            1,
        )

    def test_existing_account_different_case(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["registerUser"]
            .resolver(
                self=Mock(),
                info=info,
                email="GRAHAM@brightonandhovealbion.com",
                password="sussexbythesea1901",
                password_repeat="sussexbythesea1901",
            )
        )

        self.assertEqual(
            result,
            RegisterUser(
                success=False,
                error="An account for that email address already exists.",
            ),
        )

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username__iexact="graham@brightonandhovealbion.com",
            ).count(),
            1,
        )

    def test_invalid_email(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["registerUser"]
            .resolver(
                self=Mock(),
                info=info,
                email="this is not an email",
                password="sussexbythesea1901",
                password_repeat="sussexbythesea1901",
            )
        )

        self.assertEqual(
            result,
            RegisterUser(success=False, error="Please provide a valid email address.",),
        )

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="this is not an email",
            ).count(),
            0,
        )

    def test_nonmatching_passwords(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["registerUser"]
            .resolver(
                self=Mock(),
                info=info,
                email="lewis@brightonandhovealbion.com",
                password="sussexbythesea1901",
                password_repeat="woopsthisiswrong",
            )
        )

        self.assertEqual(
            result, RegisterUser(success=False, error="Passwords don't match.",)
        )

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="lewis@brightonandhovealbion.com",
            ).count(),
            0,
        )

    def test_weak_password(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["registerUser"]
            .resolver(
                self=Mock(),
                info=info,
                email="lewis@brightonandhovealbion.com",
                password="password",
                password_repeat="password",
            )
        )

        self.assertEqual(
            result, RegisterUser(success=False, error=INVALID_PASSWORD_MESSAGE,)
        )

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="lewis@brightonandhovealbion.com",
            ).count(),
            0,
        )
