from django.core.management.base import BaseCommand

from howsmytrack.core.models import FeedbackGroupsUser


MIN_RATINGS_TO_CONSIDER = 3
MAX_RATINGS_TO_CONSIDER = 15


class Command(BaseCommand):
    """
    Calculate average ratings for all users; run once per day via clock.py

    Users are assigned ratings by calculating the moving average of their last 15 ratings.
    """
    help = "Refresh all users' ratings."

    def add_arguments(self, parser):
        pass

    def calculate_rating(self, user):
        # In the worst case, a user's rating needs 8 requests to be calculated
        # e.g. if user has been in groups of 2, which is rubbish.
        feedback_responses = user.feedback_responses.filter(
            submitted=True,
            rating__isnull=False,
        ).order_by(
            '-time_submitted'
        ).all()[:MAX_RATINGS_TO_CONSIDER]

        # Don't assign a user a rating until they have a few
        # under their belt.
        if len(feedback_responses) < MIN_RATINGS_TO_CONSIDER:
            self.stdout.write(f"Did not update {user.email}'s rating as they only have {len(feedback_responses)} ratings.")
            return

        ratings = [
            feedback_response.rating
            for feedback_response in feedback_responses
        ]
        rating = sum(ratings) / len(ratings)

        user.rating = rating
        user.save()

        self.stdout.write(f"Updated {user.email}'s rating to {rating}.")

    def handle(self, *args, **options):
        all_users = FeedbackGroupsUser.objects.all()
        for user in all_users:
            self.calculate_rating(user)

        self.stdout.write(self.style.SUCCESS(f'Updated ratings for {len(all_users)} users.'))
