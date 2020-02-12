from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse


USER_ACCOUNTS = [
    ('graham@brightonandhovealbion.com', 2.1),
    ('glenn@brightonandhovealbion.com', 2.2),
    ('maty@brightonandhovealbion.com', 2.3),
    ('lewis@brightonandhovealbion.com', 2.4),
    ('shane@brightonandhovealbion.com', 2.5),
    ('dale@brightonandhovealbion.com', 2.6),
    ('davy@brightonandhovealbion.com', 2.7),
    ('neal@brightonandhovealbion.com', 2.8),
    ('aaron@brightonandhovealbion.com', 2.9),
    ('alireza@brightonandhovealbion.com', 3),
]


class AssignGroupsTest(TestCase):
    def setUp(self):
        self.users = []
        for email, rating in USER_ACCOUNTS:
            user = FeedbackGroupsUser.create(
                email=email,
                password='password',
            )
            user.rating = rating
            user.save()
            self.users.append(user)


    def test_assign_groups_singleton(self):
        # Use feedback requests equal to a multiple of 4 i.e. evenly sized groups
        users = self.users[:1]
        for user in users:
            FeedbackRequest(
                user=user,
                media_url='https://soundcloud.com/ruairidx/grey',
                email_when_grouped=True,
            ).save()

        call_command('assign_groups')

        # Assert no groups were created for just one user.
        self.assertEqual(FeedbackGroup.objects.count(), 0)

        # Assert no emails were sent
        self.assertEqual(len(mail.outbox), 0)


    def test_assign_groups_even_groups(self):
        # Use feedback requests equal to a multiple of 4 i.e. evenly sized groups
        users = self.users[:4]
        for user in users:
            FeedbackRequest(
                user=user,
                media_url='https://soundcloud.com/ruairidx/grey',
                email_when_grouped=True,
            ).save()

        call_command('assign_groups')

        # Assert one group was created and that responses were
        # created for everyone in the group.
        self.assertEqual(FeedbackGroup.objects.count(), 1)
        self.assertEqual(FeedbackResponse.objects.count(), 12)
        self.assertEqual(FeedbackRequest.objects.count(), 4)

        feedback_group = FeedbackGroup.objects.first()
        feedback_requests = FeedbackRequest.objects.all()

        for feedback_request in feedback_requests:
            self.assertEqual(feedback_request.feedback_group, feedback_group)

        for user in users:
            self.assertEqual(
                FeedbackResponse.objects.filter(
                    user=user,
                ).count(),
                3,
            )

        # assert correct emails were sent
        self.assertEqual(len(mail.outbox), 4)
        for i in range(0, 4):
            email = mail.outbox[i]
            self.assertEqual(email.subject, "how's my track? - your new feedback group")
            self.assertEqual(len(email.recipients()), 1)
            self.assertEqual(email.recipients()[0], users[i].email)
            self.assertTrue('https://howsmytrack.com/group/1' in email.body)


    def test_no_email_if_email_when_grouped_false(self):
        # Use feedback requests equal to a multiple of 4 i.e. evenly sized groups
        users = self.users[:4]
        for user in users:
            FeedbackRequest(
                user=user,
                media_url='https://soundcloud.com/ruairidx/grey',
                email_when_grouped=False,
            ).save()

        call_command('assign_groups')

        # Assert one group was created and that responses were
        # created for everyone in the group.
        self.assertEqual(FeedbackGroup.objects.count(), 1)
        self.assertEqual(FeedbackResponse.objects.count(), 12)
        self.assertEqual(FeedbackRequest.objects.count(), 4)

        # assert no emails were sent even though users were grouped
        self.assertEqual(len(mail.outbox), 0)

    def test_assign_groups_ignore_old_requests(self):
        # Assert that we ignore feedback requests that already have feedback groups
        users = self.users[:4]
        old_feedback_group = FeedbackGroup(name='nothing really')
        old_feedback_group.save()
        for user in users:
            # First user's request already has a feedback group.
            if user == users[0]:
                FeedbackRequest(
                    user=user,
                    media_url='https://soundcloud.com/ruairidx/grey',
                    feedback_group=old_feedback_group,
                    email_when_grouped=True,
                ).save()
            else:
                FeedbackRequest(
                    user=user,
                    media_url='https://soundcloud.com/ruairidx/grey',
                    email_when_grouped=True,
                ).save()

        call_command('assign_groups')

        # Assert one group was created (excluding old group) and that responses were
        # created for everyone in the group.
        self.assertEqual(FeedbackGroup.objects.count(), 2)
        self.assertEqual(FeedbackResponse.objects.count(), 6)

        # New group, not old_feedback_group
        feedback_group = FeedbackGroup.objects.last()

        # Check we didn't overwrite the old request or anything stupid.
        self.assertEqual(
            FeedbackRequest.objects.filter(
                user=users[0],
                feedback_group=old_feedback_group
            ).count(),
            1
        )

        for user in users[1:4]:
            self.assertEqual(
                FeedbackRequest.objects.filter(
                    user=user,
                    feedback_group=feedback_group
                ).count(),
                1
            )

        # assert correct emails were sent (not to user in old group)
        self.assertEqual(len(mail.outbox), 3)
        for i in range(0, 3):
            email = mail.outbox[i]
            self.assertEqual(email.subject, "how's my track? - your new feedback group")
            self.assertEqual(len(email.recipients()), 1)
            self.assertEqual(email.recipients()[0], users[i + 1].email)
            self.assertTrue('https://howsmytrack.com/group/2' in email.body)

    def test_assign_groups_uneven_groups(self):
        # Use an abnormal number of feedback requests to force uneven groups.
        users = self.users[:7]
        for user in users:
            FeedbackRequest(
                user=user,
                media_url='https://soundcloud.com/ruairidx/grey',
                email_when_grouped=True,
            ).save()

        call_command('assign_groups')

        # Assert two groups were created of the expected sizes.
        self.assertEqual(FeedbackRequest.objects.count(), 7)
        self.assertEqual(FeedbackGroup.objects.count(), 2)
        all_feedback_groups = FeedbackGroup.objects.all()
        self.assertEqual(
            all_feedback_groups[0].feedback_requests.count(),
            4,
        )
        self.assertEqual(
            all_feedback_groups[1].feedback_requests.count(),
            3,
        )

        self.assertEqual(FeedbackResponse.objects.count(), 12 + 6)

        users.sort(key=lambda user: user.rating, reverse=True)

        for user in users[0:4]:
            # Top four users by rating should be in first group
            self.assertEqual(
                FeedbackRequest.objects.filter(
                    user=user,
                    feedback_group=all_feedback_groups[0]
                ).count(),
                1
            )

        for user in users[4:7]:
            # Bottom three users by rating should be in second group
            self.assertEqual(
                FeedbackRequest.objects.filter(
                    user=user,
                    feedback_group=all_feedback_groups[1]
                ).count(),
                1
            )

        # assert correct emails were sent
        self.assertEqual(len(mail.outbox), 7)

        for i in range(0, 4):
            email = mail.outbox[i]
            self.assertEqual(email.subject, "how's my track? - your new feedback group")
            self.assertEqual(len(email.recipients()), 1)
            # Need to do some funny indexing because emails are sent in reverse order
            # i.e. lowest rated member of group has email sent first
            self.assertEqual(email.recipients()[0], users[3 - i].email)
            self.assertTrue('https://howsmytrack.com/group/1' in email.body)

        for i in range(4, 7):
            email = mail.outbox[i]
            self.assertEqual(email.subject, "how's my track? - your new feedback group")
            self.assertEqual(len(email.recipients()), 1)
            self.assertEqual(email.recipients()[0], users[4 + 6 - i].email)
            self.assertTrue('https://howsmytrack.com/group/2' in email.body)

    def test_assign_groups_uneven_groups_advanced(self):
        # Groups should be a minimum of 3 members
        # (unless this is literally impossible e.g. 2 or 5 requests)
        users = self.users[:10]
        for user in users:
            FeedbackRequest(
                user=user,
                media_url='https://soundcloud.com/ruairidx/grey',
                email_when_grouped=True,
            ).save()

        call_command('assign_groups')

        # Assert three groups were created of the expected sizes.
        self.assertEqual(FeedbackRequest.objects.count(), 10)
        self.assertEqual(FeedbackGroup.objects.count(), 3)
        all_feedback_groups = FeedbackGroup.objects.all()
        self.assertEqual(
            all_feedback_groups[0].feedback_requests.count(),
            4,
        )
        self.assertEqual(
            all_feedback_groups[1].feedback_requests.count(),
            3,
        )
        self.assertEqual(
            all_feedback_groups[2].feedback_requests.count(),
            3,
        )

        self.assertEqual(FeedbackResponse.objects.count(), 12 + 6 + 6)

        users.sort(key=lambda user: user.rating, reverse=True)

        for user in users[0:4]:
            # Top four users by rating should be in first group
            self.assertEqual(
                FeedbackRequest.objects.filter(
                    user=user,
                    feedback_group=all_feedback_groups[0]
                ).count(),
                1
            )

        for user in users[4:7]:
            # Next three users by rating should be in second group
            self.assertEqual(
                FeedbackRequest.objects.filter(
                    user=user,
                    feedback_group=all_feedback_groups[1]
                ).count(),
                1
            )

        for user in users[7:10]:
            # Bottom three users by rating should be in third group
            self.assertEqual(
                FeedbackRequest.objects.filter(
                    user=user,
                    feedback_group=all_feedback_groups[2]
                ).count(),
                1
            )
