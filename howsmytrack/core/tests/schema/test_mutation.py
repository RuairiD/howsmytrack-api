from unittest.mock import Mock
from unittest.mock import patch

import graphql_jwt
from django.test import TestCase
from graphene.test import Client

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import MediaTypeChoice
from howsmytrack.core.schema.mutation import CreateFeedbackRequest
from howsmytrack.core.schema.mutation import EditFeedbackRequest
from howsmytrack.core.schema.mutation import INVALID_MEDIA_URL_MESSAGE
from howsmytrack.core.schema.mutation import INVALID_PASSWORD_MESSAGE
from howsmytrack.core.schema.mutation import RateFeedbackResponse
from howsmytrack.core.schema.mutation import RefreshTokenFromCookie
from howsmytrack.core.schema.mutation import RegisterUser
from howsmytrack.core.schema.mutation import SubmitFeedbackResponse
from howsmytrack.core.schema.types import FeedbackRequestType
from howsmytrack.core.schema.types import FeedbackResponseType
from howsmytrack.core.schema.types import UserType
from howsmytrack.core.schema.types import FeedbackGroupType
from howsmytrack.schema import schema


class RefreshTokenFromCookieTest(TestCase):
    def test_refresh_token_from_cookie(self):
        context = Mock()
        info = Mock()
        info.context = Mock()
        info.context.COOKIES = { 'JWT': 'existingtoken' }
        with patch.object(
            graphql_jwt.Refresh,
            'mutate',
            return_value=RefreshTokenFromCookie(
                token='newtoken',
            ),
        ) as mock_mutate:
            result = schema.get_mutation_type().fields['refreshTokenFromCookie'].resolver(
                context,
                info,
            )
            mock_mutate.assert_called_once_with(context, info, token='existingtoken')

    def test_refresh_token_without_cookies(self):
        context = Mock()
        info = Mock()
        info.context = Mock()
        info.context.COOKIES = {}
        with patch.object(
            graphql_jwt.Refresh,
            'mutate',
            return_value=RefreshTokenFromCookie(
                token='newtoken',
            ),
        ) as mock_mutate:
            result = schema.get_mutation_type().fields['refreshTokenFromCookie'].resolver(
                context,
                info,
            )
            self.assertIsNone(result)


class RegisterUserTest(TestCase):
    def setUp(self):
        self.user = FeedbackGroupsUser.create(
            email='graham@brightonandhovealbion.com',
            password='password',
        )
        self.user.save()

    def test_no_account(self):
        info = Mock()
        result = schema.get_mutation_type().fields['registerUser'].resolver(
            self=Mock(),
            info=info,
            email='lewis@brightonandhovealbion.com',
            password='sussexbythesea1901',
            password_repeat='sussexbythesea1901',
        )

        self.assertEqual(result, RegisterUser(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username='lewis@brightonandhovealbion.com',
            ).count(),
            1
        )

    def test_existing_account(self):
        info = Mock()
        result = schema.get_mutation_type().fields['registerUser'].resolver(
            self=Mock(),
            info=info,
            email='graham@brightonandhovealbion.com',
            password='sussexbythesea1901',
            password_repeat='sussexbythesea1901',
        )

        self.assertEqual(result, RegisterUser(
            success=False,
            error="An account for that email address already exists.",
        ))

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username='graham@brightonandhovealbion.com',
            ).count(),
            1
        )

    def test_invalid_email(self):
        info = Mock()
        result = schema.get_mutation_type().fields['registerUser'].resolver(
            self=Mock(),
            info=info,
            email='this is not an email',
            password='sussexbythesea1901',
            password_repeat='sussexbythesea1901',
        )

        self.assertEqual(result, RegisterUser(
            success=False,
            error="Please provide a valid email address.",
        ))

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username='this is not an email',
            ).count(),
            0,
        )

    def test_nonmatching_passwords(self):
        info = Mock()
        result = schema.get_mutation_type().fields['registerUser'].resolver(
            self=Mock(),
            info=info,
            email='lewis@brightonandhovealbion.com',
            password='sussexbythesea1901',
            password_repeat='woopsthisiswrong',
        )

        self.assertEqual(result, RegisterUser(
            success=False,
            error="Passwords don't match.",
        ))

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username='lewis@brightonandhovealbion.com',
            ).count(),
            0,
        )

    def test_weak_password(self):
        info = Mock()
        result = schema.get_mutation_type().fields['registerUser'].resolver(
            self=Mock(),
            info=info,
            email='lewis@brightonandhovealbion.com',
            password='password',
            password_repeat='password',
        )

        self.assertEqual(result, RegisterUser(
            success=False,
            error=INVALID_PASSWORD_MESSAGE,
        ))

        self.assertEqual(
            FeedbackGroupsUser.objects.filter(
                user__username='lewis@brightonandhovealbion.com',
            ).count(),
            0,
        )


class CreateFeedbackRequestTest(TestCase):
    def setUp(self):
        self.user = FeedbackGroupsUser.create(
            email='graham@brightonandhovealbion.com',
            password='password',
        )
        self.user.save()

    def test_logged_out(self):
        info = Mock()
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://soundcloud.com/ruairidx/bruno',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=False,
            error='Not logged in.',
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
            ).count(),
            0,
        )

    def test_invalid_url(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='not a real url',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=False,
            error=INVALID_MEDIA_URL_MESSAGE,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
            ).count(),
            0,
        )

    def test_unsupported_platform(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://twitter.com/ruairidx',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=False,
            error=INVALID_MEDIA_URL_MESSAGE,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
            ).count(),
            0,
        )

    def test_soundcloud(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://soundcloud.com/ruairidx/bruno',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://soundcloud.com/ruairidx/bruno',
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt='feedback_prompt',
            ).count(),
            1,
        )

    def test_googledrive(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://drive.google.com/file/d/roflcopter/view',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://drive.google.com/file/d/roflcopter/view',
                media_type=MediaTypeChoice.GOOGLEDRIVE.name,
                feedback_prompt='feedback_prompt',
            ).count(),
            1,
        )

    def test_dropbox(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://www.dropbox.com/s/nonsense/file.wav',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://www.dropbox.com/s/nonsense/file.wav',
                media_type=MediaTypeChoice.DROPBOX.name,
                feedback_prompt='feedback_prompt',
            ).count(),
            1,
        )

    def test_existing_unassigned_request(self):
        # Add a previous unassigned request, should prevent adding another.
        FeedbackRequest(
            user=self.user,
            media_url='https://soundcloud.com/ruairidx/bruno',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            feedback_group=None,
        ).save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://www.dropbox.com/s/nonsense/file.wav',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=False,
            error='You have an unassigned feedback request. Once that request has been assigned to a feedback group, you will be eligible to submit another request.',
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
            ).count(),
            1,
        )

    def test_existing_assigned_request(self):
        # Add a previous assigned request, user should be able to add another.
        feedback_group = FeedbackGroup(name='name')
        feedback_group.save()

        FeedbackRequest(
            user=self.user,
            media_url='https://soundcloud.com/ruairidx/bruno',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            feedback_group=feedback_group,
        ).save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://www.dropbox.com/s/nonsense/file.wav',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://www.dropbox.com/s/nonsense/file.wav',
                media_type=MediaTypeChoice.DROPBOX.name,
                feedback_prompt='feedback_prompt',
            ).count(),
            1,
        )

    def test_same_url_different_account(self):
        self.another_user = FeedbackGroupsUser.create(
            email='lewis@brightonandhovealbion.com',
            password='password',
        )
        self.another_user.save()
        # Add a previous unassigned request, should prevent adding another.
        FeedbackRequest(
            user=self.another_user,
            media_url='https://soundcloud.com/ruairidx/bruno',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
        ).save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://soundcloud.com/ruairidx/bruno',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=False,
            error='A request for this track is already pending.',
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                media_url='https://soundcloud.com/ruairidx/bruno',
                user=self.user,
            ).count(),
            0,
        )


class EditFeedbackRequestTest(TestCase):
    def setUp(self):
        self.user = FeedbackGroupsUser.create(
            email='graham@brightonandhovealbion.com',
            password='password',
        )
        self.user.save()

        self.existing_request = FeedbackRequest(
            user=self.user,
            media_url='https://soundcloud.com/ruairidx/grey',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
        )
        self.existing_request.save()

    def test_logged_out(self):
        info = Mock()
        result = schema.get_mutation_type().fields['editFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            feedback_request_id=self.existing_request.id,
            media_url='https://soundcloud.com/ruairidx/bruno',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, EditFeedbackRequest(
            success=False,
            error='Not logged in.',
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://soundcloud.com/ruairidx/bruno',
            ).count(),
            0,
        )

    def test_invalid_url(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['editFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            feedback_request_id=self.existing_request.id,
            media_url='not a real url',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, EditFeedbackRequest(
            success=False,
            error=INVALID_MEDIA_URL_MESSAGE,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://soundcloud.com/ruairidx/grey',
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt='feedback_prompt',
            ).count(),
            1,
        )

    def test_unsupported_platform(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['editFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            feedback_request_id=self.existing_request.id,
            media_url='https://twitter.com/ruairidx',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, EditFeedbackRequest(
            success=False,
            error=INVALID_MEDIA_URL_MESSAGE,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://soundcloud.com/ruairidx/grey',
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt='feedback_prompt',
            ).count(),
            1,
        )

    def test_valid_url(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['editFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            feedback_request_id=self.existing_request.id,
            media_url='https://www.dropbox.com/s/nonsense/file.wav',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://www.dropbox.com/s/nonsense/file.wav',
                media_type=MediaTypeChoice.DROPBOX.name,
                feedback_prompt='feedback_prompt',
            ).count(),
            1,
        )

    def test_assigned_request(self):
        feedback_group = FeedbackGroup(name='name')
        feedback_group.save()
        self.existing_request.feedback_group = feedback_group
        self.existing_request.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['editFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            feedback_request_id=self.existing_request.id,
            media_url='https://www.dropbox.com/s/nonsense/file.wav',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, EditFeedbackRequest(
            success=False,
            error='This request has already been assigned to a feedback group and cannot be edited.',
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://soundcloud.com/ruairidx/grey',
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt='feedback_prompt',
            ).count(),
            1,
        )

    def test_unauthorised(self):
        self.new_user = FeedbackGroupsUser.create(
            email='lewis@brightonandhovealbion.com',
            password='password',
        )
        self.new_user.save() 
        info = Mock()
        info.context = Mock()
        info.context.user = self.new_user.user
        result = schema.get_mutation_type().fields['editFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            feedback_request_id=self.existing_request.id,
            media_url='https://www.dropbox.com/s/nonsense/file.wav',
            feedback_prompt='feedback_prompt',
        )

        self.assertEqual(result, EditFeedbackRequest(
            success=False,
            error='You are not the owner of this feedback request.',
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://soundcloud.com/ruairidx/grey',
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt='feedback_prompt',
            ).count(),
            1,
        )


class SubmitFeedbackResponseTest(TestCase):
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
        )
        self.feedback_request.save()

        self.feedback_response = FeedbackResponse(
            user=self.response_user,
            feedback_request=self.feedback_request,
        )
        self.feedback_response.save()

    def test_logged_out(self):
        info = Mock()
        result = schema.get_mutation_type().fields['submitFeedbackResponse'].resolver(
            self=Mock(),
            info=info,
            feedback_response_id=self.feedback_response.id,
            feedback='feedback',
        )

        self.assertEqual(result, SubmitFeedbackResponse(
            success=False,
            error='Not logged in.',
        ))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback='feedback',
                submitted=True,
            ).count(),
            0,
        )

    def test_bad_id(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.response_user.user
        result = schema.get_mutation_type().fields['submitFeedbackResponse'].resolver(
            self=Mock(),
            info=info,
            feedback_response_id=1901,
            feedback='feedback',
        )

        self.assertEqual(result, SubmitFeedbackResponse(
            success=False,
            error='Invalid feedback_response_id',
        ))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback='feedback',
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
        result = schema.get_mutation_type().fields['submitFeedbackResponse'].resolver(
            self=Mock(),
            info=info,
            feedback_response_id=self.feedback_response.id,
            feedback='feedback',
        )

        self.assertEqual(result, SubmitFeedbackResponse(
            success=False,
            error='Feedback has already been submitted',
        ))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback='feedback',
                submitted=True,
            ).count(),
            0,
        )

    def test_logged_in_unsubmitted(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.response_user.user
        result = schema.get_mutation_type().fields['submitFeedbackResponse'].resolver(
            self=Mock(),
            info=info,
            feedback_response_id=self.feedback_response.id,
            feedback='feedback',
        )

        self.assertEqual(result, SubmitFeedbackResponse(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackResponse.objects.filter(
                user=self.response_user,
                feedback_request=self.feedback_request,
                feedback='feedback',
                submitted=True,
            ).count(),
            1,
        )


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
