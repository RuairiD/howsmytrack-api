from unittest.mock import Mock

from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import MediaTypeChoice
from howsmytrack.core.models import GenreChoice
from howsmytrack.core.schema.mutations.delete_feedback_request import DeleteFeedbackRequest
from howsmytrack.schema import schema


class DeleteFeedbackRequestTest(TestCase):
    def setUp(self):
        self.user = FeedbackGroupsUser.create(
            email='graham@brightonandhovealbion.com',
            password='password',
        )
        self.user.save()
        self.other_user = FeedbackGroupsUser.create(
            email='lewis@brightonandhovealbion.com',
            password='password',
        )
        self.other_user.save()

        self.existing_request = FeedbackRequest(
            user=self.user,
            media_url='https://soundcloud.com/ruairidx/grey',
            media_type=MediaTypeChoice.SOUNDCLOUD.name,
            feedback_prompt='feedback_prompt',
            email_when_grouped=True,
            genre=GenreChoice.HIPHOP.name,
        )
        self.existing_request.save()

    def test_logged_out(self):
        info = Mock()
        result = schema.get_mutation_type().fields['deleteFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            feedback_request_id=self.existing_request.id,
        )

        self.assertEqual(result, DeleteFeedbackRequest(
            success=False,
            error='Not logged in.',
        ))

        self.assertEqual(
            FeedbackRequest.objects.count(),
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
        result = schema.get_mutation_type().fields['deleteFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            feedback_request_id=self.existing_request.id,
        )

        self.assertEqual(result, DeleteFeedbackRequest(
            success=False,
            error='This request has already been assigned to a feedback group and cannot be edited.',
        ))

        self.assertEqual(
            FeedbackRequest.objects.count(),
            1,
        )

    def test_unauthorised(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.other_user.user
        result = schema.get_mutation_type().fields['deleteFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            feedback_request_id=self.existing_request.id,
        )

        self.assertEqual(result, DeleteFeedbackRequest(
            success=False,
            error='You are not the owner of this feedback request.',
        ))

        self.assertEqual(
            FeedbackRequest.objects.count(),
            1,
        )

    def test_ok(self):
        info = Mock()
        info.context = Mock()
        info.context.user = self.user.user
        result = schema.get_mutation_type().fields['deleteFeedbackRequest'].resolver(
            self=Mock(),
            info=info,
            feedback_request_id=self.existing_request.id,
        )

        self.assertEqual(result, DeleteFeedbackRequest(
            success=True,
            error=None,
        ))

        self.assertEqual(
            FeedbackRequest.objects.count(),
            0,
        )
