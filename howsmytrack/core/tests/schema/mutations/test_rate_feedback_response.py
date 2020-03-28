from unittest.mock import Mock

from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import MediaTypeChoice
from howsmytrack.core.models import GenreChoice
from howsmytrack.core.schema.mutations.rate_feedback_response import RateFeedbackResponse
from howsmytrack.schema import schema


class RateFeedbackResponseTest(TestCase):
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
            submitted=True
        )
        self.feedback_response.save()

    def test_logged_out(self):
        info = Mock()
        result = schema.get_mutation_type().fields['rateFeedbackResponse'].resolver(
            self=Mock(),
            info=info,
            feedback_response_id=self.feedback_response.id,
            rating=3,
        )

        self.assertEqual(result, RateFeedbackResponse(
            success=False,
            error='Not logged in.',
        ))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback='feedback',
                submitted=True,
                rating=None,
            ).count(),
            1,
        )

    def test_bad_id(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.request_user.user
        result = schema.get_mutation_type().fields['rateFeedbackResponse'].resolver(
            self=Mock(),
            info=info,
            feedback_response_id=1901,
            rating=3,
        )

        self.assertEqual(result, RateFeedbackResponse(
            success=False,
            error='Invalid feedback_response_id',
        ))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback='feedback',
                rating=None,
            ).count(),
            1,
        )

    def test_bad_rating(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.request_user.user
        result = schema.get_mutation_type().fields['rateFeedbackResponse'].resolver(
            self=Mock(),
            info=info,
            feedback_response_id=self.feedback_response.id,
            rating=10,
        )

        self.assertEqual(result, RateFeedbackResponse(
            success=False,
            error='Invalid rating',
        ))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback='feedback',
                rating=None,
            ).count(),
            1,
        )

    def test_not_submitted(self):
        self.feedback_response.submitted = False
        self.feedback_response.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.request_user.user
        result = schema.get_mutation_type().fields['rateFeedbackResponse'].resolver(
            self=Mock(),
            info=info,
            feedback_response_id=self.feedback_response.id,
            rating=3,
        )

        self.assertEqual(result, RateFeedbackResponse(
            success=False,
            error='This feedback has not been submitted and cannot be rated.',
        ))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback='feedback',
                submitted=False,
                rating=None,
            ).count(),
            1,
        )

    def test_already_rated(self):
        self.feedback_response.rating = 5
        self.feedback_response.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.request_user.user
        result = schema.get_mutation_type().fields['rateFeedbackResponse'].resolver(
            self=Mock(),
            info=info,
            feedback_response_id=self.feedback_response.id,
            rating=3,
        )

        self.assertEqual(result, RateFeedbackResponse(
            success=False,
            error='Feedback has already been rated',
        ))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback='feedback',
                submitted=True,
                rating=5,
            ).count(),
            1,
        )

    def test_logged_in_submitted(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.request_user.user
        result = schema.get_mutation_type().fields['rateFeedbackResponse'].resolver(
            self=Mock(),
            info=info,
            feedback_response_id=self.feedback_response.id,
            rating=3,
        )

        self.assertEqual(result, RateFeedbackResponse(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback='feedback',
                submitted=True,
                rating=3,
            ).count(),
            1,
        )
