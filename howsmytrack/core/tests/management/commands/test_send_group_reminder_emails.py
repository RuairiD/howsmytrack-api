import datetime
from unittest.mock import Mock
from unittest.mock import patch

import pytz
from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import MediaTypeChoice


NOW = datetime.datetime(2020, 2, 16, 6, tzinfo=pytz.utc)
FUTURE = datetime.datetime(2020, 2, 17, 6, tzinfo=pytz.utc)
GROUP_TIME_CREATED = datetime.datetime(2020, 2, 16, 3, tzinfo=pytz.utc)  # 3 hours ago


class SendGroupReminderEmailsTest(TestCase):
    def setUp(self):
        self.graham_user = FeedbackGroupsUser.create(
            email="graham@brightonandhovealbion.com", password="password",
        )
        self.lewis_user = FeedbackGroupsUser.create(
            email="lewis@brightonandhovealbion.com", password="password",
        )
        self.graham_user.save()
        self.lewis_user.save()

        with patch("django.utils.timezone.now", Mock(return_value=GROUP_TIME_CREATED)):
            self.feedback_group = FeedbackGroup(name="name")
            self.feedback_group.save()

        self.graham_feedback_request = FeedbackRequest(
            user=self.graham_user,
            media_url="https://soundcloud.com/ruairidx/grey",
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt="feedback_prompt",
            feedback_group=self.feedback_group,
            email_when_grouped=True,
        )
        self.lewis_feedback_request = FeedbackRequest(
            user=self.lewis_user,
            media_url="https://soundcloud.com/ruairidx/bruno",
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt="feedback_prompt",
            feedback_group=self.feedback_group,
            email_when_grouped=True,
        )
        self.graham_feedback_request.save()
        self.lewis_feedback_request.save()

        self.graham_feedback_response = FeedbackResponse(
            feedback_request=self.lewis_feedback_request,
            user=self.graham_user,
            submitted=False,
        )
        self.lewis_feedback_response = FeedbackResponse(
            feedback_request=self.graham_feedback_request,
            user=self.lewis_user,
            submitted=False,
        )
        self.graham_feedback_response.save()
        self.lewis_feedback_response.save()

    def test_send_reminders_to_all(self):
        with patch("django.utils.timezone.now", Mock(return_value=FUTURE)):
            call_command("send_group_reminder_emails")

        # Assert emails were sent to both
        self.assertEqual(len(mail.outbox), 2)

        self.graham_feedback_request.refresh_from_db()
        self.lewis_feedback_request.refresh_from_db()
        self.assertTrue(self.graham_feedback_request.reminder_email_sent)
        self.assertTrue(self.lewis_feedback_request.reminder_email_sent)

    def test_do_not_send_reminder_if_not_email_when_grouped(self):
        self.lewis_feedback_request.email_when_grouped = False
        self.lewis_feedback_request.save()

        with patch("django.utils.timezone.now", Mock(return_value=FUTURE)):
            call_command("send_group_reminder_emails")

        # Assert email was only sent to graham
        self.assertEqual(len(mail.outbox), 1)

        self.graham_feedback_request.refresh_from_db()
        self.lewis_feedback_request.refresh_from_db()
        self.assertTrue(self.graham_feedback_request.reminder_email_sent)
        self.assertFalse(self.lewis_feedback_request.reminder_email_sent)

    def test_do_not_send_reminder_if_already_sent(self):
        self.lewis_feedback_request.reminder_email_sent = True
        self.lewis_feedback_request.save()

        with patch("django.utils.timezone.now", Mock(return_value=FUTURE)):
            call_command("send_group_reminder_emails")

        # Assert email was only sent to graham
        self.assertEqual(len(mail.outbox), 1)

        self.graham_feedback_request.refresh_from_db()
        self.lewis_feedback_request.refresh_from_db()
        self.assertTrue(self.graham_feedback_request.reminder_email_sent)

    def test_do_not_send_reminder_if_too_soon(self):
        self.lewis_user.send_reminder_emails = False
        self.lewis_user.save()

        with patch("django.utils.timezone.now", Mock(return_value=FUTURE)):
            call_command("send_group_reminder_emails")

        # Assert email was only sent to graham
        self.assertEqual(len(mail.outbox), 1)

        self.graham_feedback_request.refresh_from_db()
        self.lewis_feedback_request.refresh_from_db()
        self.assertTrue(self.graham_feedback_request.reminder_email_sent)
        self.assertFalse(self.lewis_feedback_request.reminder_email_sent)

    def test_do_not_send_reminder_if_user_disabled_send_reminder_emails(self):
        self.lewis_user.send_reminder_emails = False
        self.lewis_user.save()

        with patch("django.utils.timezone.now", Mock(return_value=FUTURE)):
            call_command("send_group_reminder_emails")

        self.assertEqual(len(mail.outbox), 1)

        self.graham_feedback_request.refresh_from_db()
        self.lewis_feedback_request.refresh_from_db()
        self.assertTrue(self.graham_feedback_request.reminder_email_sent)
        self.assertFalse(self.lewis_feedback_request.reminder_email_sent)

    def test_do_not_send_reminder_if_unassigned(self):
        self.lewis_feedback_request.feedback_group = None
        self.lewis_feedback_request.save()
        self.graham_feedback_request.feedback_group = None
        self.graham_feedback_request.save()

        with patch("django.utils.timezone.now", Mock(return_value=FUTURE)):
            call_command("send_group_reminder_emails")

        self.assertEqual(len(mail.outbox), 0)

        self.graham_feedback_request.refresh_from_db()
        self.lewis_feedback_request.refresh_from_db()
        self.assertFalse(self.graham_feedback_request.reminder_email_sent)
        self.assertFalse(self.lewis_feedback_request.reminder_email_sent)

    def test_do_not_send_reminder_if_response_submitted(self):
        self.lewis_feedback_response.submitted = True
        self.lewis_feedback_response.save()

        with patch("django.utils.timezone.now", Mock(return_value=FUTURE)):
            call_command("send_group_reminder_emails")

        self.assertEqual(len(mail.outbox), 1)

        self.graham_feedback_request.refresh_from_db()
        self.lewis_feedback_request.refresh_from_db()
        self.assertTrue(self.graham_feedback_request.reminder_email_sent)
        self.assertFalse(self.lewis_feedback_request.reminder_email_sent)

    def test_trackless_request(self):
        self.lewis_feedback_request.media_url = None
        self.lewis_feedback_request.save()

        with patch("django.utils.timezone.now", Mock(return_value=FUTURE)):
            call_command("send_group_reminder_emails")

        self.assertEqual(len(mail.outbox), 2)

        self.lewis_feedback_request.refresh_from_db()
        self.assertTrue(self.lewis_feedback_request.reminder_email_sent)
        # Really crude way to check that the trackless email template was used.
        self.assertTrue(
            "Don't forget to check out your feedback group and write feedback for its other members!"
            in mail.outbox[1].body
        )
