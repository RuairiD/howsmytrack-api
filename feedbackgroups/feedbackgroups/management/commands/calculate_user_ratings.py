from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from feedbackgroups.feedbackgroups.models import FeedbackGroupsUser
from feedbackgroups.feedbackgroups.models import FeedbackGroup
from feedbackgroups.feedbackgroups.models import FeedbackRequest
from feedbackgroups.feedbackgroups.models import FeedbackResponse

MIN_RATINGS_TO_CONSIDER = 5
MAX_RATINGS_TO_CONSIDER = 15

class Command(BaseCommand):
    """
    
    """
    help = "Refresh all users' ratings."

    def add_arguments(self, parser):
        pass

    def calculate_rating(self, user):
        # In the worst case, a user's rating needs 8 requests to be calculated
        # e.g. if user has been in groups of 2, which is rubbish.
        feedback_responses = user.feedback_responses.filter(
            submitted=True,
        ).order_by(
            '-time_submitted'
        ).all()[:MAX_RATINGS_TO_CONSIDER]

        # Don't assign a user a rating until they have a few
        # under their belt.
        if len(feedback_responses) < MIN_RATINGS_TO_CONSIDER:
            return

        ratings = [
            feedback_response.rating
            for feedback_response in feedback_responses
        ]
        rating = sum(ratings)/len(ratings)

        user.rating = rating
        user.save()

    def handle(self, *args, **options):
        all_users = FeedbackGroupsUser.objects.all()
        for user in all_users:
            self.calculate_rating(user)
        