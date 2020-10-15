from unittest.mock import Mock

from django.test import TestCase

from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import GenreChoice
from howsmytrack.core.models import MediaTypeChoice
from howsmytrack.core.schema.mutations.edit_feedback_request import EditFeedbackRequest
from howsmytrack.core.validators import INVALID_MEDIA_URL_MESSAGE
from howsmytrack.schema import schema


class EditFeedbackRequestTest(TestCase):
    def setUp(self):
        self.user = FeedbackGroupsUser.create(
            email="graham@brightonandhovealbion.com", password="password",
        )
        self.user.save()

        self.existing_request = FeedbackRequest(
            user=self.user,
            media_url="https://soundcloud.com/ruairidx/grey",
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt="feedback_prompt",
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )
        self.existing_request.save()

    def test_logged_out(self):
        info = Mock()
        result = (
            schema.get_mutation_type()
            .fields["editFeedbackRequest"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_request_id=self.existing_request.id,
                media_url="https://soundcloud.com/ruairidx/bruno",
                feedback_prompt="feedback_prompt",
                email_when_grouped=False,
                genre=GenreChoice.HIPHOP.name,
            )
        )

        self.assertEqual(
            result,
            EditFeedbackRequest(
                success=False, error="Not logged in.", invalid_media_url=False,
            ),
        )

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url="https://soundcloud.com/ruairidx/bruno",
                genre=GenreChoice.HIPHOP.name,
            ).count(),
            0,
        )

    def test_invalid_url(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = (
            schema.get_mutation_type()
            .fields["editFeedbackRequest"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_request_id=self.existing_request.id,
                media_url="not a real url",
                feedback_prompt="feedback_prompt",
                email_when_grouped=False,
                genre=GenreChoice.HIPHOP.name,
            )
        )

        self.assertEqual(
            result,
            EditFeedbackRequest(
                success=False, error=INVALID_MEDIA_URL_MESSAGE, invalid_media_url=True,
            ),
        )

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url="https://soundcloud.com/ruairidx/grey",
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt="feedback_prompt",
                genre=GenreChoice.ELECTRONIC.name,
            ).count(),
            1,
        )

    def test_unsupported_platform(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = (
            schema.get_mutation_type()
            .fields["editFeedbackRequest"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_request_id=self.existing_request.id,
                media_url="https://twitter.com/ruairidx",
                feedback_prompt="feedback_prompt",
                email_when_grouped=False,
                genre=GenreChoice.HIPHOP.name,
            )
        )

        self.assertEqual(
            result,
            EditFeedbackRequest(
                success=False, error=INVALID_MEDIA_URL_MESSAGE, invalid_media_url=True,
            ),
        )

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url="https://soundcloud.com/ruairidx/grey",
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt="feedback_prompt",
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
            ).count(),
            1,
        )

    def test_valid_url(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = (
            schema.get_mutation_type()
            .fields["editFeedbackRequest"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_request_id=self.existing_request.id,
                media_url="https://www.dropbox.com/s/nonsense/file.wav",
                feedback_prompt="feedback_prompt",
                email_when_grouped=False,
                genre=GenreChoice.HIPHOP.name,
            )
        )

        self.assertEqual(
            result,
            EditFeedbackRequest(success=True, error=None, invalid_media_url=False,),
        )

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url="https://www.dropbox.com/s/nonsense/file.wav",
                media_type=MediaTypeChoice.DROPBOX.name,
                feedback_prompt="feedback_prompt",
                email_when_grouped=False,
                genre=GenreChoice.HIPHOP.name,
            ).count(),
            1,
        )

    def test_assigned_request(self):
        feedback_group = FeedbackGroup(name="name")
        feedback_group.save()
        self.existing_request.feedback_group = feedback_group
        self.existing_request.save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = (
            schema.get_mutation_type()
            .fields["editFeedbackRequest"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_request_id=self.existing_request.id,
                media_url="https://www.dropbox.com/s/nonsense/file.wav",
                feedback_prompt="feedback_prompt",
                email_when_grouped=False,
                genre=GenreChoice.HIPHOP.name,
            )
        )

        self.assertEqual(
            result,
            EditFeedbackRequest(
                success=False,
                error="This request has already been assigned to a feedback group and cannot be edited.",
                invalid_media_url=False,
            ),
        )

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url="https://soundcloud.com/ruairidx/grey",
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt="feedback_prompt",
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
            ).count(),
            1,
        )

    def test_unauthorised(self):
        self.new_user = FeedbackGroupsUser.create(
            email="lewis@brightonandhovealbion.com", password="password",
        )
        self.new_user.save()
        info = Mock()
        info.context = Mock()
        info.context.user = self.new_user.user
        result = (
            schema.get_mutation_type()
            .fields["editFeedbackRequest"]
            .resolver(
                self=Mock(),
                info=info,
                feedback_request_id=self.existing_request.id,
                media_url="https://www.dropbox.com/s/nonsense/file.wav",
                feedback_prompt="feedback_prompt",
                email_when_grouped=False,
                genre=GenreChoice.HIPHOP.name,
            )
        )

        self.assertEqual(
            result,
            EditFeedbackRequest(
                success=False,
                error="You are not the owner of this feedback request.",
                invalid_media_url=False,
            ),
        )

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url="https://soundcloud.com/ruairidx/grey",
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt="feedback_prompt",
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
            ).count(),
            1,
        )
