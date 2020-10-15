from unittest.mock import Mock

from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import GenreChoice
from howsmytrack.core.models import MediaTypeChoice
from howsmytrack.core.schema.mutations.submit_feedback_response import (
    SubmitFeedbackResponse,
)
from howsmytrack.schema import schema


class SubmitFeedbackResponseTest(TestCase):
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
            user=self.response_user, feedback_request=self.feedback_request,
        )
        self.feedback_response.save()

    def test_logged_out(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["submitFeedbackResponse"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=self.feedback_response.id,
                feedback="feedback",
                allow_replies=True,
            )
        )

        self.assertEqual(
            result, SubmitFeedbackResponse(success=False, error="Not logged in.",)
        )

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback="feedback",
                submitted=True,
            ).count(),
            0,
        )

    def test_bad_id(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.response_user.user
        result = (
            schema.get_mutation_type()
            .fields["submitFeedbackResponse"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=1901,
                feedback="feedback",
                allow_replies=True,
            )
        )

        self.assertEqual(
            result,
            SubmitFeedbackResponse(
                success=False, error="Invalid feedback_response_id",
            ),
        )

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback="feedback",
                submitted=True,
            ).count(),
            0,
        )

    def test_already_submitted(self):
        self.feedback_response.submitted = True
        self.feedback_response.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.response_user.user
        result = (
            schema.get_mutation_type()
            .fields["submitFeedbackResponse"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=self.feedback_response.id,
                feedback="feedback",
                allow_replies=True,
            )
        )

        self.assertEqual(
            result,
            SubmitFeedbackResponse(
                success=False, error="Feedback has already been submitted",
            ),
        )

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback="feedback",
                submitted=True,
            ).count(),
            0,
        )

    def test_logged_in_unsubmitted(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.response_user.user
        result = (
            schema.get_mutation_type()
            .fields["submitFeedbackResponse"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_response_id=self.feedback_response.id,
                feedback="feedback",
                allow_replies=True,
            )
        )

        self.assertEqual(result, SubmitFeedbackResponse(success=True, error=None,))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback="feedback",
                submitted=True,
                allow_replies=True,
            ).count(),
            1,
        )
