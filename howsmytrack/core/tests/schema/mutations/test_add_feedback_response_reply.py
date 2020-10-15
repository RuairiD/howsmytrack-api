from unittest.mock import Mock

from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import FeedbackResponseReply
from howsmytrack.core.models import GenreChoice
from howsmytrack.core.models import MediaTypeChoice
from howsmytrack.core.schema.mutation import AddFeedbackResponseReply
from howsmytrack.core.schema.types import FeedbackResponseReplyType
from howsmytrack.schema import schema


class AddFeedbackResponseReplyTest(TestCase):
    def setUp(self):
        self.request_user = FeedbackGroupsUser.create(
            email="graham@brightonandhovealbion.com", password="password",
        )
        self.request_user.save()
        self.response_user = FeedbackGroupsUser.create(
            email="lewis@brightonandhovealbion.com", password="password",
        )
        self.response_user.save()

        self.feedback_request = FeedbackRequest(
            user=self.request_user,
            media_url="https://soundcloud.com/ruairidx/grey",
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt="feedback_prompt",
            genre=GenreChoice.HIPHOP.name,
        )
        self.feedback_request.save()

        self.feedback_response = FeedbackResponse(
            user=self.response_user,
            feedback_request=self.feedback_request,
            feedback="feedback",
            submitted=True,
            allow_replies=True,
        )
        self.feedback_response.save()

    def test_logged_out(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["addFeedbackResponseReply"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=self.feedback_response.id,
                text="thanks pal",
                allow_replies=True,
            )
        )

        self.assertEqual(
            result, AddFeedbackResponseReply(reply=None, error="Not logged in.",)
        )

        self.assertEqual(
            FeedbackResponseReply.objects.filter(
                feedback_response=self.feedback_response,
            ).count(),
            0,
        )

    def test_bad_id(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.request_user.user
        result = (
            schema.get_mutation_type()
            .fields["addFeedbackResponseReply"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=1901,
                text="thanks pal",
                allow_replies=True,
            )
        )

        self.assertEqual(
            result,
            AddFeedbackResponseReply(reply=None, error="Invalid feedback_response_id",),
        )

        self.assertEqual(
            FeedbackResponseReply.objects.filter(
                feedback_response=self.feedback_response,
            ).count(),
            0,
        )

    def test_invalid_user(self):
        unrelated_user = FeedbackGroupsUser.create(
            email="maty@brightonandhovealbion.com", password="password",
        )
        unrelated_user.save()

        info = Mock()
        info.context = Mock()
        info.context.user = unrelated_user.user
        result = (
            schema.get_mutation_type()
            .fields["addFeedbackResponseReply"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=self.feedback_response.id,
                text="thanks pal",
                allow_replies=True,
            )
        )

        self.assertEqual(
            result,
            AddFeedbackResponseReply(
                reply=None, error="You are not authorised to reply to this feedback.",
            ),
        )

        self.assertEqual(
            FeedbackResponseReply.objects.filter(
                feedback_response=self.feedback_response,
            ).count(),
            0,
        )

    def test_reject_reply_if_not_feedback_response_allow_replies(self):
        self.feedback_response.allow_replies = False
        self.feedback_response.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.feedback_request.user.user
        result = (
            schema.get_mutation_type()
            .fields["addFeedbackResponseReply"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=self.feedback_response.id,
                text="thanks pal",
                allow_replies=True,
            )
        )

        self.assertEqual(
            result,
            AddFeedbackResponseReply(
                reply=None, error="You cannot reply to this feedback.",
            ),
        )

        self.assertEqual(
            FeedbackResponseReply.objects.filter(
                feedback_response=self.feedback_response,
            ).count(),
            0,
        )

    def test_reject_reply_if_not_existing_reply_allow_replies(self):
        existing_reply = FeedbackResponseReply(
            feedback_response=self.feedback_response,
            user=self.feedback_request.user,
            text="danke mate",
            allow_replies=False,
        )
        existing_reply.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.feedback_response.user.user
        result = (
            schema.get_mutation_type()
            .fields["addFeedbackResponseReply"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=self.feedback_response.id,
                text="thanks pal",
                allow_replies=True,
            )
        )

        self.assertEqual(
            result,
            AddFeedbackResponseReply(
                reply=None, error="You cannot reply to this feedback.",
            ),
        )

        self.assertEqual(
            FeedbackResponseReply.objects.filter(
                feedback_response=self.feedback_response,
            ).count(),
            1,
        )

    def test_reject_reply_if_response_is_unsubmitted(self):
        self.feedback_response.submitted = False
        self.feedback_response.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.feedback_response.user.user
        result = (
            schema.get_mutation_type()
            .fields["addFeedbackResponseReply"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=self.feedback_response.id,
                text="thanks pal",
                allow_replies=True,
            )
        )

        self.assertEqual(
            result,
            AddFeedbackResponseReply(
                reply=None, error="You cannot reply to this feedback.",
            ),
        )

        self.assertEqual(
            FeedbackResponseReply.objects.filter(
                feedback_response=self.feedback_response,
            ).count(),
            0,
        )

    def test_successful_reply(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.feedback_request.user.user
        result = (
            schema.get_mutation_type()
            .fields["addFeedbackResponseReply"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=self.feedback_response.id,
                text="thanks pal",
                allow_replies=True,
            )
        )

        self.assertEqual(
            FeedbackResponseReply.objects.filter(
                feedback_response=self.feedback_response,
                user=self.feedback_request.user,
                text="thanks pal",
                allow_replies=True,
            ).count(),
            1,
        )

        reply = FeedbackResponseReply.objects.filter(
            feedback_response=self.feedback_response,
            user=self.feedback_request.user,
            text="thanks pal",
            allow_replies=True,
        ).first()

        self.assertEqual(
            result,
            AddFeedbackResponseReply(
                reply=FeedbackResponseReplyType(
                    id=1,
                    username="You",
                    text="thanks pal",
                    allow_replies=True,
                    time_created=reply.time_created,
                ),
                error=None,
            ),
        )
