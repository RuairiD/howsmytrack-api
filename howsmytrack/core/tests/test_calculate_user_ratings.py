import pytz
from datetime import datetime

from django.core.management import call_command
from django.test import TestCase

from howsmytrack.core.management.commands.calculate_user_ratings import MIN_RATINGS_TO_CONSIDER
from howsmytrack.core.management.commands.calculate_user_ratings import MAX_RATINGS_TO_CONSIDER
from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse


EMAIL_DOMAIN = '@brightonandhovealbion.com'


class CalculateUserRatingsTest(TestCase):
    def setUp(self):
        self.users = []
        for i in range(0, MAX_RATINGS_TO_CONSIDER * 2 + 1):
            user = FeedbackGroupsUser.create(
                email=f'{i}{EMAIL_DOMAIN}',
                password='password',
            )
            user.save()
            self.users.append(user)

    def test_calculate_user_rating(self):
        user = self.users[0]
        for i in range(0, MIN_RATINGS_TO_CONSIDER):
            feedback_request = FeedbackRequest(
                user=self.users[i],
                soundcloud_url='https://soundcloud.com/ruairidx/bruno',
            )
            feedback_request.save()
            FeedbackResponse(
                feedback_request=feedback_request,
                user=user,
                feedback='jery get ipad',
                submitted=True,
                time_submitted=datetime.fromtimestamp(i, tz=pytz.UTC),
                rating=5,
            ).save()

        call_command('calculate_user_ratings')

        updated_user = FeedbackGroupsUser.objects.filter(
            id=user.id,
        ).first()

        self.assertEquals(updated_user.rating, 5)

    def test_calculate_user_rating_without_enough_rating(self):
        user = self.users[0]
        for i in range(0, MIN_RATINGS_TO_CONSIDER - 1):
            feedback_request = FeedbackRequest(
                user=self.users[i],
                soundcloud_url='https://soundcloud.com/ruairidx/bruno',
            )
            feedback_request.save()
            FeedbackResponse(
                feedback_request=feedback_request,
                user=user,
                feedback='jery get ipad',
                submitted=True,
                time_submitted=datetime.fromtimestamp(i, tz=pytz.UTC),
                rating=5,
            ).save()

        call_command('calculate_user_ratings')

        updated_user = FeedbackGroupsUser.objects.filter(
            id=user.id,
        ).first()

        self.assertEquals(updated_user.rating, 0)

    def test_calculate_user_rating_with_many_ratings(self):
        user = self.users[0]
        for i in range(0, MAX_RATINGS_TO_CONSIDER * 2):
            feedback_request = FeedbackRequest(
                user=self.users[i],
                soundcloud_url='https://soundcloud.com/ruairidx/bruno',
            )
            feedback_request.save()
            # Old rates will be good, new ratings will be a little worse.
            # The newer ratings should prevail.
            if i < MAX_RATINGS_TO_CONSIDER:
                rating = 5
            else:
                rating = 3
            FeedbackResponse(
                feedback_request=feedback_request,
                user=user,
                feedback='jery get ipad',
                submitted=True,
                time_submitted=datetime.fromtimestamp(i, tz=pytz.UTC),
                rating=rating,
            ).save()

        call_command('calculate_user_ratings')

        updated_user = FeedbackGroupsUser.objects.filter(
            id=user.id,
        ).first()

        # Calculated from most recent ratings, ignoring old ones.
        self.assertEquals(updated_user.rating, 3)

