from unittest.mock import Mock

from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import MediaTypeChoice
from howsmytrack.core.models import GenreChoice
from howsmytrack.core.schema.mutations.create_feedback_request import CreateFeedbackRequest
from howsmytrack.core.validators import INVALID_MEDIA_URL_MESSAGE
from howsmytrack.schema import schema


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
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=False,
            error='Not logged in.',
            invalid_media_url=False,
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
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=False,
            error=INVALID_MEDIA_URL_MESSAGE,
            invalid_media_url=True,
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
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=False,
            error=INVALID_MEDIA_URL_MESSAGE,
            invalid_media_url=True,
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
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=True,
            error=None,
            invalid_media_url=False,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://soundcloud.com/ruairidx/bruno',
                media_type=MediaTypeChoice.SOUNDCLOUD.name,
                feedback_prompt='feedback_prompt',
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
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
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=True,
            error=None,
            invalid_media_url=False,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://drive.google.com/file/d/roflcopter/view',
                media_type=MediaTypeChoice.GOOGLEDRIVE.name,
                feedback_prompt='feedback_prompt',
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
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
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=True,
            error=None,
            invalid_media_url=False,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://www.dropbox.com/s/nonsense/file.wav',
                media_type=MediaTypeChoice.DROPBOX.name,
                feedback_prompt='feedback_prompt',
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
            ).count(),
            1,
        )

    def test_onedrive(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://onedrive.live.com/?authkey=AUTHKEY&cid=CID&id=ID',
            feedback_prompt='feedback_prompt',
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=True,
            error=None,
            invalid_media_url=False,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://onedrive.live.com/?authkey=AUTHKEY&cid=CID&id=ID',
                media_type=MediaTypeChoice.ONEDRIVE.name,
                feedback_prompt='feedback_prompt',
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
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
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        ).save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://www.dropbox.com/s/nonsense/file.wav',
            feedback_prompt='feedback_prompt',
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=False,
            error='You have an unassigned feedback request. Once that request has been assigned to a feedback group, you will be eligible to submit another request.',
            invalid_media_url=False,
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
            email_when_grouped=True,
            genre=GenreChoice.HIPHOP.name,
        ).save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://www.dropbox.com/s/nonsense/file.wav',
            feedback_prompt='feedback_prompt',
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=True,
            error=None,
            invalid_media_url=False,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=self.user,
                media_url='https://www.dropbox.com/s/nonsense/file.wav',
                media_type=MediaTypeChoice.DROPBOX.name,
                feedback_prompt='feedback_prompt',
                email_when_grouped=True,
                genre=GenreChoice.ELECTRONIC.name,
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
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        ).save()

        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['createFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            media_url='https://soundcloud.com/ruairidx/bruno',
            feedback_prompt='feedback_prompt',
            email_when_grouped=True,
            genre=GenreChoice.ELECTRONIC.name,
        )

        self.assertEqual(result, CreateFeedbackRequest(
            success=False,
            error='A request for this track is already pending.',
            invalid_media_url=False,
        ))

        self.assertEqual(
            FeedbackRequest.objects.filter(
                media_url='https://soundcloud.com/ruairidx/bruno',
                user=self.user,
            ).count(),
            0,
        )
