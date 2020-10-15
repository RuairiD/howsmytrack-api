from unittest.mock import Mock

from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.schema.mutations.update_send_reminder_emails import (
    UpdateSendReminderEmails,
)
from howsmytrack.schema import schema


class UpdateSendReminderEmailsTest(TestCase):
    def setUp(self):
        self.user = FeedbackGroupsUser.create(
            email="graham@brightonandhovealbion.com", password="password",
        )
        self.user.save()

    def test_not_logged_in(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["updateSendReminderEmails"]
            .resolver(self=Mock(), info=info, send_reminder_emails=False,)
        )

        self.assertEqual(
            result, UpdateSendReminderEmails(success=False, error="Not logged in.",)
        )

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="graham@brightonandhovealbion.com",
                send_reminder_emails=True,
            ).count(),
            1,
        )

    def test_logged_in(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = (
            schema.get_mutation_type()
            .fields["updateSendReminderEmails"]
            .resolver(self=Mock(), info=info, send_reminder_emails=False,)
        )

        self.assertEqual(result, UpdateSendReminderEmails(success=True, error=None,))

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username="graham@brightonandhovealbion.com",
                send_reminder_emails=False,
            ).count(),
            1,
        )
