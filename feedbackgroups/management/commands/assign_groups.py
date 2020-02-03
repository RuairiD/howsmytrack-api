from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from feedbackgroups.models import FeedbackGroup
from feedbackgroups.models import FeedbackRequest
from feedbackgroups.models import FeedbackResponse

FEEDBACK_GROUP_SIZE = 4

class Command(BaseCommand):
    help = 'Creates FeedbackGroups for all unassigned feedback requests'

    def add_arguments(self, parser):
        pass

    def create_feedback_group(self, feedback_requests):
        feedback_group = FeedbackGroup(name='test replace lol')
        feedback_group.save()

        for feedback_request in feedback_requests:
            feedback_request.feedback_group = feedback_group
            feedback_request.save()

            # Create empty feedback responses for each request-user pairing in the group.
            for other_feedback_request in feedback_requests:
                if feedback_request != other_feedback_request:
                    feedback_response = FeedbackResponse(
                        feedback_request=feedback_request,
                        user=other_feedback_request.user,
                    )
                    feedback_response.save()

    def handle(self, *args, **options):
        unassigned_feedback_requests = FeedbackRequest.objects.filter(
            feedback_group=None,
        ).order_by(
            '-user__rating',
        ).all()

        for i in range(0, len(unassigned_feedback_requests), FEEDBACK_GROUP_SIZE):
            self.create_feedback_group(unassigned_feedback_requests[i:i + FEEDBACK_GROUP_SIZE])

