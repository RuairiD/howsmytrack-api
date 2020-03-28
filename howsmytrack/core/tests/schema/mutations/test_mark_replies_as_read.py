from unittest.mock import Mock

from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import FeedbackResponseReply
from howsmytrack.core.models import MediaTypeChoice
from howsmytrack.core.models import GenreChoice
from howsmytrack.core.schema.mutation import MarkRepliesAsRead
from howsmytrack.schema import schema


class MarkRepliesAsReadTest(TestCase):
    def setUp(self):
        self.request_user = FeedbackGroupsUser.create(
            email='graham@brightonandhovealbion.com',
            password='password',
        )
        self.request_user.save()
        self.response_user = FeedbackGroupsUser.create(
            email='lewis@brightonandhovealbion.com',
            password='password',
        )
        self.response_user.save()

        self.feedback_request = FeedbackRequest(
            user=self.request_user,
            media_url='https://soundcloud.com/ruairidx/grey',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            genre=GenreChoice.HIPHOP.name,
        )
        self.feedback_request.save()

        self.feedback_response = FeedbackResponse(
            user=self.response_user,
            feedback_request=self.feedback_request,
            feedback='feedback',
            submitted=True,
            allow_replies=True,
        )
        self.feedback_response.save()

        self.feedback_response_reply = FeedbackResponseReply(
            feedback_response=self.feedback_response,
            user=self.request_user,
            text='this is a reply',
            allow_replies=True,
        )
        self.feedback_response_reply.save()

    def test_logged_out(self):
        info = Mock()
        result = schema.get_mutation_type().fields['markRepliesAsRead'].resolver(
            self=Mock(),
            info=info,
            reply_ids=[1],
        )

        self.assertEqual(result, MarkRepliesAsRead(
            success=False,
            error='Not logged in.',
        ))

        self.assertEqual(
            FeedbackResponseReply.objects.filter(
                time_read__isnull=True,
            ).count(),
            1,
        )

    def test_invalid_user(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.request_user.user
        result = schema.get_mutation_type().fields['markRepliesAsRead'].resolver(
            self=Mock(),
            info=info,
            reply_ids=[1],
        )

        self.assertEqual(result, MarkRepliesAsRead(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackResponseReply.objects.filter(
                time_read__isnull=True,
            ).count(),
            1,
        )

    def test_valid_user(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.response_user.user
        result = schema.get_mutation_type().fields['markRepliesAsRead'].resolver(
            self=Mock(),
            info=info,
            reply_ids=[1],
        )

        self.assertEqual(result, MarkRepliesAsRead(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackResponseReply.objects.filter(
                time_read__isnull=False,
                id=1,
            ).count(),
            1,
        )
