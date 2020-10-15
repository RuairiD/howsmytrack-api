from unittest.mock import Mock

from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.schema.mutations.update_email import UpdateEmail
from howsmytrack.schema import schema


class UpdateEmailTest(TestCase):
    def setUp(self):
        self.user = FeedbackGroupsUser.create(
            email="graham@brightonandhovealbion.com", password="password",
        )
        self.user.save()

    def test_not_logged_in(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["updateEmail"]
            .resolver(self=Mock(), info=info, email="lewis@brightonandhovealbion.com",)
        )

        self.assertEqual(result, UpdateEmail(success=False, error="Not logged in.",))

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="graham@brightonandhovealbion.com",
            ).count(),
            1,
        )
        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="lewis@brightonandhovealbion.com",
            ).count(),
            0,
        )

    def test_existing_account_with_email(self):
        other_user = FeedbackGroupsUser.create(
            email="lewis@brightonandhovealbion.com", password="password",
        )
        other_user.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = (
            schema.get_mutation_type()
            .fields["updateEmail"]
            .resolver(self=Mock(), info=info, email="lewis@brightonandhovealbion.com",)
        )

        self.assertEqual(
            result,
            UpdateEmail(
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
        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="lewis@brightonandhovealbion.com",
            ).count(),
            1,
        )

    def test_invalid_email(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = (
            schema.get_mutation_type()
            .fields["updateEmail"]
            .resolver(self=Mock(), info=info, email="not an email address",)
        )

        self.assertEqual(
            result,
            UpdateEmail(success=False, error="Please provide a valid email address.",),
        )

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="graham@brightonandhovealbion.com",
            ).count(),
            1,
        )
        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="not an email address",
            ).count(),
            0,
        )

    def test_valid_email(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = (
            schema.get_mutation_type()
            .fields["updateEmail"]
            .resolver(self=Mock(), info=info, email="lewis@brightonandhovealbion.com",)
        )

        self.assertEqual(result, UpdateEmail(success=True, error=None,))

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="graham@brightonandhovealbion.com",
            ).count(),
            0,
        )
        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="lewis@brightonandhovealbion.com",
            ).count(),
            1,
        )
