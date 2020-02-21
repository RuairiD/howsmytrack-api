import datetime
import pytz
from unittest.mock import Mock
from unittest.mock import patch

from django.test import TestCase
from graphene.test import Client

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import MediaTypeChoice
from howsmytrack.core.models import GenreChoice
from howsmytrack.core.schema.types import FeedbackRequestType
from howsmytrack.core.schema.types import FeedbackResponseType
from howsmytrack.core.schema.types import UserType
from howsmytrack.core.schema.types import FeedbackGroupType
from howsmytrack.core.schema.types import MediaInfoType
from howsmytrack.schema import schema


DEFAULT_DATETIME = datetime.datetime(1991, 11, 21, tzinfo=pytz.utc)


class UserDetailsTest(TestCase):
    def setUp(self):
        self.user = FeedbackGroupsUser.create(
            email='graham@brightonandhovealbion.com',
            password='password',
        )
        self.user.rating = 4.5
        self.user.save()

    def test_user_details_logged_out(self):
        info = Mock()
        result = schema.get_query_type().graphene_type().resolve_user_details(
            info=info,
        )
        self.assertIs(result, None)

    def test_user_details_logged_in(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_query_type().graphene_type().resolve_user_details(
            info=info,
        )
        self.assertEqual(result, UserType(
            username='graham@brightonandhovealbion.com',
            rating=4.5,
            incomplete_responses=0,
        ))

    def test_user_details_logged_in_incomplete_response(self):
        other_user = FeedbackGroupsUser.create(
            email='lewis@brightonandhovealbion.com',
            password='password',
        )
        other_user.save()

        feedback_group = FeedbackGroup(name='name')
        feedback_group.save()

        feedback_request = FeedbackRequest(
            user=other_user,
            media_url='https://soundcloud.com/ruairidx/grey',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            feedback_group=feedback_group,
            email_when_grouped=True,
            genre=GenreChoice.NO_GENRE,
        )
        feedback_request.save()
        
        feedback_response = FeedbackResponse(
            feedback_request=feedback_request,
            user=self.user,
        )
        feedback_response.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_query_type().graphene_type().resolve_user_details(
            info=info,
        )
        self.assertEqual(result, UserType(
            username='graham@brightonandhovealbion.com',
            rating=4.5,
            incomplete_responses=1,
        ))


class MediaInfoTest(TestCase):
    def test_invalid_url(self):
        info = Mock()
        result = schema.get_query_type().graphene_type().resolve_media_info(
            info=info,
            media_url='https://twitter.com',
        )
        self.assertEqual(result, MediaInfoType(
            media_url='https://twitter.com',
            media_type=None,
        ))

    def test_valid_url(self):
        info = Mock()
        result = schema.get_query_type().graphene_type().resolve_media_info(
            info=info,
            media_url='https://soundcloud.com/ruairidx/bruno',
        )
        self.assertEqual(result, MediaInfoType(
            media_url='https://soundcloud.com/ruairidx/bruno',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
        ))


class FeedbackGroupTest(TestCase):
    def setUp(self):
        self.graham_user = FeedbackGroupsUser.create(
            email='graham@brightonandhovealbion.com',
            password='password',
        )
        self.lewis_user = FeedbackGroupsUser.create(
            email='lewis@brightonandhovealbion.com',
            password='password',
        )
        self.graham_user.save()
        self.lewis_user.save()

        with patch('django.utils.timezone.now', Mock(return_value=DEFAULT_DATETIME)):
            self.feedback_group = FeedbackGroup(name='name')
            self.feedback_group.save()

        self.graham_feedback_request = FeedbackRequest(
            user=self.graham_user,
            media_url='https://soundcloud.com/ruairidx/grey',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            feedback_group=self.feedback_group,
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )
        self.lewis_feedback_request = FeedbackRequest(
            user=self.lewis_user,
            media_url='https://soundcloud.com/ruairidx/bruno',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            feedback_group=self.feedback_group,
            email_when_grouped=True,
            genre=GenreChoice.HIPHOP.name,
        )
        self.graham_feedback_request.save()
        self.lewis_feedback_request.save()

        self.graham_feedback_response = FeedbackResponse(
            feedback_request=self.lewis_feedback_request,
            user=self.graham_user,
            feedback='grahamfeedback',
            submitted=True,
            rating=4,
        )
        self.lewis_feedback_response = FeedbackResponse(
            feedback_request=self.graham_feedback_request,
            user=self.lewis_user,
            feedback='lewisfeedback',
            submitted=True,
            rating=3,
        )
        self.graham_feedback_response.save()
        self.lewis_feedback_response.save()

    def test_logged_out(self):
        info = Mock()
        result = schema.get_query_type().graphene_type().resolve_feedback_group(
            info=info,
            feedback_group_id=self.feedback_group.id,
        )
        self.assertIs(result, None)

    def test_bad_id(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.graham_user.user
        result = schema.get_query_type().graphene_type().resolve_feedback_group(
            info=info,
            feedback_group_id=1901,
        )
        self.assertIs(result, None)

    def test_logged_in(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.graham_user.user
        result = schema.get_query_type().graphene_type().resolve_feedback_group(
            info=info,
            feedback_group_id=self.feedback_group.id,
        )
        expected = FeedbackGroupType(
            id=self.feedback_group.id,
            name='name',
            media_url='https://soundcloud.com/ruairidx/grey',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_request=FeedbackRequestType(
                id=1,
                media_url='https://soundcloud.com/ruairidx/grey',
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt='feedback_prompt',
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
            ),
            time_created=DEFAULT_DATETIME,
            members=2,
            feedback_responses=[
                FeedbackResponseType(
                    id=1,
                    feedback_request=FeedbackRequestType(
                        id=2,
                        media_url='https://soundcloud.com/ruairidx/bruno',
                        media_type=MediaTypeChoice.SOUNDCLOUD.name,
                        feedback_prompt='feedback_prompt',
                        email_when_grouped=True,
                        genre=GenreChoice.HIPHOP.name,
                    ),
                    feedback='grahamfeedback',
                    submitted=True,
                    rating=4,
                )
            ],
            user_feedback_responses=[
                FeedbackResponseType(
                    id=2,
                    feedback_request=FeedbackRequestType(
                        id=1,
                        media_url='https://soundcloud.com/ruairidx/grey',
                        media_type=MediaTypeChoice.SOUNDCLOUD.name,
                        feedback_prompt='feedback_prompt',
                        email_when_grouped=True,
                        genre=GenreChoice.ELECTRONIC.name,
                    ),
                    feedback='lewisfeedback',
                    submitted=True,
                    rating=3,
                )
            ],
            user_feedback_response_count=1,
        )
        self.assertEqual(result, expected)

    def test_logged_in_without_submitting_feedback(self):
        self.graham_feedback_response.submitted = False
        self.graham_feedback_response.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.graham_user.user
        result = schema.get_query_type().graphene_type().resolve_feedback_group(
            info=info,
            feedback_group_id=self.feedback_group.id,
        )
        expected = FeedbackGroupType(
            id=self.feedback_group.id,
            name='name',
            media_url='https://soundcloud.com/ruairidx/grey',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_request=FeedbackRequestType(
                id=1,
                media_url='https://soundcloud.com/ruairidx/grey',
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt='feedback_prompt',
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
            ),
            time_created=DEFAULT_DATETIME,
            members=2,
            feedback_responses=[
                FeedbackResponseType(
                    id=1,
                    feedback_request=FeedbackRequestType(
                        id=2,
                        media_url='https://soundcloud.com/ruairidx/bruno',
                        media_type=MediaTypeChoice.SOUNDCLOUD.name,
                        feedback_prompt='feedback_prompt',
                        email_when_grouped=True,
                        genre=GenreChoice.HIPHOP.name,
                    ),
                    feedback='grahamfeedback',
                    submitted=False,
                    rating=4,
                )
            ],
            user_feedback_responses=None,
            # Should still show user that count is 1 even if we don't
            # send the actual response itself.
            user_feedback_response_count=1,
        )
        self.assertEqual(result, expected)


class FeedbackGroupsTest(TestCase):
    def setUp(self):
        self.graham_user = FeedbackGroupsUser.create(
            email='graham@brightonandhovealbion.com',
            password='password',
        )
        self.lewis_user = FeedbackGroupsUser.create(
            email='lewis@brightonandhovealbion.com',
            password='password',
        )
        self.graham_user.save()
        self.lewis_user.save()

        with patch('django.utils.timezone.now', Mock(return_value=DEFAULT_DATETIME)):
            self.feedback_group = FeedbackGroup(name='name')
            self.feedback_group.save()

        self.graham_feedback_request = FeedbackRequest(
            user=self.graham_user,
            media_url='https://soundcloud.com/ruairidx/grey',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            feedback_group=self.feedback_group,
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )
        self.lewis_feedback_request = FeedbackRequest(
            user=self.lewis_user,
            media_url='https://soundcloud.com/ruairidx/bruno',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            feedback_group=self.feedback_group,
            email_when_grouped=True,
            genre=GenreChoice.HIPHOP.name,
        )
        self.graham_feedback_request.save()
        self.lewis_feedback_request.save()

        self.graham_feedback_response = FeedbackResponse(
            feedback_request=self.lewis_feedback_request,
            user=self.graham_user,
            feedback='grahamfeedback',
            submitted=True,
            rating=4,
        )
        self.lewis_feedback_response = FeedbackResponse(
            feedback_request=self.graham_feedback_request,
            user=self.lewis_user,
            feedback='lewisfeedback',
            submitted=True,
            rating=3,
        )
        self.graham_feedback_response.save()
        self.lewis_feedback_response.save()

    def test_logged_out(self):
        info = Mock()
        result = schema.get_query_type().graphene_type().resolve_feedback_groups(
            info=info,
        )
        self.assertEqual(result, [])

    def test_logged_in(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.graham_user.user
        result = schema.get_query_type().graphene_type().resolve_feedback_groups(
            info=info,
        )
        expected = [FeedbackGroupType(
            id=self.feedback_group.id,
            name='name',
            media_url='https://soundcloud.com/ruairidx/grey',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_request=FeedbackRequestType(
                id=1,
                media_url='https://soundcloud.com/ruairidx/grey',
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt='feedback_prompt',
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
            ),
            time_created=DEFAULT_DATETIME,
            members=2,
            feedback_responses=[
                FeedbackResponseType(
                    id=1,
                    feedback_request=FeedbackRequestType(
                        id=2,
                        media_url='https://soundcloud.com/ruairidx/bruno',
                        media_type=MediaTypeChoice.SOUNDCLOUD.name,
                        feedback_prompt='feedback_prompt',
                        email_when_grouped=True,
                        genre=GenreChoice.HIPHOP.name,
                    ),
                    feedback='grahamfeedback',
                    submitted=True,
                    rating=4,
                )
            ],
            user_feedback_responses=[
                FeedbackResponseType(
                    id=2,
                    feedback_request=FeedbackRequestType(
                        id=1,
                        media_url='https://soundcloud.com/ruairidx/grey',
                        media_type=MediaTypeChoice.SOUNDCLOUD.name,
                        feedback_prompt='feedback_prompt',
                        email_when_grouped=True,
                        genre=GenreChoice.ELECTRONIC.name,
                    ),
                    feedback='lewisfeedback',
                    submitted=True,
                    rating=3,
                )
            ],
            user_feedback_response_count=1,
        )]
        self.assertEqual(result, expected)



class UnassignedRequestTest(TestCase):
    def setUp(self):
        # graham's request will be assigned, but not lewis's
        self.graham_user = FeedbackGroupsUser.create(
            email='graham@brightonandhovealbion.com',
            password='password',
        )
        self.lewis_user = FeedbackGroupsUser.create(
            email='lewis@brightonandhovealbion.com',
            password='password',
        )
        self.graham_user.save()
        self.lewis_user.save()

        self.feedback_group = FeedbackGroup(name='name')
        self.feedback_group.save()

        self.graham_feedback_request = FeedbackRequest(
            user=self.graham_user,
            media_url='https://soundcloud.com/ruairidx/grey',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            feedback_group=self.feedback_group,
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )
        self.lewis_feedback_request = FeedbackRequest(
            user=self.lewis_user,
            media_url='https://soundcloud.com/ruairidx/bruno',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            feedback_group=None,
            email_when_grouped=True,
            genre=GenreChoice.HIPHOP.name,
        )
        self.graham_feedback_request.save()
        self.lewis_feedback_request.save()

    def test_logged_out(self):
        info = Mock()
        result = schema.get_query_type().graphene_type().resolve_unassigned_request(
            info=info,
        )
        self.assertIs(result, None)

    def test_logged_in_without_unassigned_request(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.graham_user.user
        result = schema.get_query_type().graphene_type().resolve_unassigned_request(
            info=info,
        )
        
        self.assertIs(result, None)

    def test_logged_in_with_unassigned_request(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.lewis_user.user
        result = schema.get_query_type().graphene_type().resolve_unassigned_request(
            info=info,
        )
        expected = FeedbackRequestType(
            id=2,
            media_url='https://soundcloud.com/ruairidx/bruno',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            email_when_grouped=True,
            genre=GenreChoice.HIPHOP.name,
        )
        self.assertEqual(result, expected)
