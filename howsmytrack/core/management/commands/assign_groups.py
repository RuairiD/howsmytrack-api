from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse

FEEDBACK_GROUP_SIZE = 4
# Request counts of 2, 5 and 7 are weird because they're prime numbers
# that aren't 3 or 4 (which we like). We therefore hardcode what the
# next group size should be as they're odd to calculate.
REQUESTS_TO_GROUP_SIZES = dict([
    (2, 2),
    (5, 3),
    (7, 4),
])

class Command(BaseCommand):
    """
    Groups should ideally be of size 4 unless this isn't possible. In this case,
    it's fine to have some groups of size 3. What we're really trying to avoid is
    groups of size 2 as these are rubbish e.g.

    reqs  group sizes
    2     2
    3     3
    4     4
    5     3 2
    6     3 3
    7     4 3
    8     4 4
    9     3 3 3
    10    4 3 3
    11    4 4 3
    12    4 4 4
    13    4 3 3 3
    14    4 4 3 3
    15    4 4 4 3
    16    4 4 4 4
    17    4 4 3 3 3
    18    4 4 4 3 3
    19    4 4 4 4 3
    20    4 4 4 4 4
    21    4 4 4 3 3 3
    etc.
    """
    help = 'Creates FeedbackGroups for all unassigned feedback requests'

    def add_arguments(self, parser):
        pass

    def create_feedback_group(self, feedback_requests):
        feedback_group = FeedbackGroup(name='test replace lol')
        feedback_group.save()

        feedback_group.name = f'Feedback Group #{feedback_group.id}'
        feedback_group.save()

        requests_count = 0
        responses_count = 0
        for feedback_request in feedback_requests:
            feedback_request.feedback_group = feedback_group
            feedback_request.save()
            requests_count += 1

            # Create empty feedback responses for each request-user pairing in the group.
            for other_feedback_request in feedback_requests:
                if feedback_request != other_feedback_request:
                    feedback_response = FeedbackResponse(
                        feedback_request=feedback_request,
                        user=other_feedback_request.user,
                    )
                    feedback_response.save()
                    responses_count += 1
        
        self.stdout.write(
            f'Created {feedback_group.name} with {requests_count} requests and {responses_count} responses.',
        )

    def handle(self, *args, **options):
        unassigned_feedback_requests = FeedbackRequest.objects.filter(
            feedback_group=None,
        ).order_by(
            '-user__rating',
        ).all()

        if len(unassigned_feedback_requests) == 1:
            # Not enough requests to make a group. Try again another time :(
            return

        # Determine the number of requests that can be added
        # groups of FEEDBACK_GROUP_SIZE. We're actively trying
        # to avoid groups of size 2 or fewer unless it's literally
        # impossible.
        i = 0
        while i < len(unassigned_feedback_requests):
            requests_left = len(unassigned_feedback_requests) - i
            if requests_left > 9 or requests_left % FEEDBACK_GROUP_SIZE == 0:
                self.create_feedback_group(
                    unassigned_feedback_requests[i:i + FEEDBACK_GROUP_SIZE]
                )
                i = i + FEEDBACK_GROUP_SIZE
            elif requests_left % 3 == 0:
                self.create_feedback_group(
                    unassigned_feedback_requests[i:i + 3]
                )
                i = i + 3
            else:
                next_group_size = REQUESTS_TO_GROUP_SIZES[requests_left]
                self.create_feedback_group(
                    unassigned_feedback_requests[i:i + next_group_size]
                )
                i = i + next_group_size
