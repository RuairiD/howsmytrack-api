from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.template.loader import render_to_string

from howsmytrack.core.models import GenreChoice
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

WEBSITE_URL = 'https://www.howsmytrack.com{path}'

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

    Requests are separated by genre before grouping, so requests of the same genre
    will be grouped together.
    """
    help = 'Creates FeedbackGroups for all unassigned feedback requests'

    def add_arguments(self, parser):
        pass

    def send_email_to_group_member(self, email, feedback_group_name, feedback_group_url, is_trackless):
        if is_trackless:
            message = render_to_string('new_group_email_trackless.txt', {
                'email': email,
                'feedback_group_name': feedback_group_name,
                'feedback_group_url': feedback_group_url,
            })
            html_message = render_to_string('new_group_email_trackless.html', {
                'email': email,
                'feedback_group_name': feedback_group_name,
                'feedback_group_url': feedback_group_url,
            })
        else:
            message = render_to_string('new_group_email.txt', {
                'email': email,
                'feedback_group_name': feedback_group_name,
                'feedback_group_url': feedback_group_url,
            })
            html_message = render_to_string('new_group_email.html', {
                'email': email,
                'feedback_group_name': feedback_group_name,
                'feedback_group_url': feedback_group_url,
            })

        send_mail(
            subject="your new feedback group",
            message=message,
            from_email=None, # Use default in settings.py
            recipient_list=[email],
            html_message=html_message,
        )

    def send_emails_for_group(self, feedback_group):
        for feedback_request in feedback_group.feedback_requests.all():
            if feedback_request.email_when_grouped:
                self.send_email_to_group_member(
                    email=feedback_request.user.email,
                    feedback_group_name=feedback_group.name,
                    feedback_group_url=WEBSITE_URL.format(
                        path=f'/group/{feedback_group.id}'
                    ),
                    is_trackless=False
                )

    def create_feedback_group(self, feedback_requests, genres):
        feedback_group = FeedbackGroup(name='test replace lol')
        feedback_group.save()

        genre_title = '/'.join([
            genre.value
            for genre in genres
        ])
        feedback_group.name = f'Feedback Group #{feedback_group.id} - {genre_title}'
        feedback_group.save()

        requests_count = 0
        responses_count = 0
        for feedback_request in feedback_requests:
            feedback_request.feedback_group = feedback_group
            feedback_request.save()
            requests_count += 1

            # TODO: try and remove this; ideally we'd just create FeedbackResponse rows
            # only when a user submits feedback.
            #
            # Create empty feedback responses for each request-user pairing in the group.
            for other_feedback_request in feedback_requests:
                if feedback_request != other_feedback_request:
                    feedback_response = FeedbackResponse(
                        feedback_request=feedback_request,
                        user=other_feedback_request.user,
                    )
                    feedback_response.save()
                    responses_count += 1

        # Send every member of the group an email with a link to the newly created group
        self.send_emails_for_group(feedback_group)
        
        self.stdout.write(
            f'Created {feedback_group.name} with {requests_count} requests and {responses_count} responses.',
        )

        return feedback_group, genres

    def assign_groups_for_requests(self, feedback_requests, genres):
        # Determine the number of requests that can be added
        # groups of FEEDBACK_GROUP_SIZE. We're actively trying
        # to avoid groups of size 2 or fewer unless it's literally
        # impossible.
        feedback_groups = []
        i = 0
        while i < len(feedback_requests):
            requests_left = len(feedback_requests) - i
            if requests_left > 9 or requests_left % FEEDBACK_GROUP_SIZE == 0:
                feedback_groups.append(self.create_feedback_group(
                    feedback_requests[i:i + FEEDBACK_GROUP_SIZE],
                    genres,
                ))
                i = i + FEEDBACK_GROUP_SIZE
            elif requests_left % 3 == 0:
                feedback_groups.append(self.create_feedback_group(
                    feedback_requests[i:i + 3],
                    genres,
                ))
                i = i + 3
            else:
                next_group_size = REQUESTS_TO_GROUP_SIZES[requests_left]
                feedback_groups.append(self.create_feedback_group(
                    feedback_requests[i:i + next_group_size],
                    genres,
                ))
                i = i + next_group_size
        return feedback_groups

    def separate_feedback_requests_by_genres(self, feedback_requests):
        all_feedback_requests_and_genres = []
        for genre in GenreChoice:
            feedback_requests_by_genre = feedback_requests.filter(
                genre=genre.name,
            ).all()
            if len(feedback_requests_by_genre) > 0:
                all_feedback_requests_and_genres.append((
                    feedback_requests_by_genre,
                    set([genre]),
                ))
        return sorted(
            all_feedback_requests_and_genres,
            key=lambda requests_and_genres: len(requests_and_genres[0]),
        )

    def merge_genres(self, all_feedback_requests_and_genres, target_index, source_index):
        target_feedback_requests, target_genres = all_feedback_requests_and_genres[target_index]
        source_feedback_requests, source_genres = all_feedback_requests_and_genres[source_index]

        merged_feedback_requests = target_feedback_requests | source_feedback_requests
        merged_genres = target_genres | source_genres

        all_feedback_requests_and_genres[target_index] = (merged_feedback_requests, merged_genres)
        all_feedback_requests_and_genres.pop(source_index)

    def handle(self, *args, **options):
        unassigned_feedback_requests = FeedbackRequest.objects.filter(
            feedback_group=None,
            media_url__isnull=False,
        ).order_by(
            '-user__rating',
        )

        if unassigned_feedback_requests.count() == 1:
            # Not enough requests to make a group. Try again another time :(
            return

        all_feedback_requests_and_genres = self.separate_feedback_requests_by_genres(
            unassigned_feedback_requests
        )

        # If any genre has < 2 submissions, merge it with the genre with the next fewest submissions.
        all_genres_valid = False
        while not all_genres_valid:
            all_genres_valid = True
            for i in range(0, len(all_feedback_requests_and_genres)):
                feedback_requests, genres = all_feedback_requests_and_genres[i]
                if len(feedback_requests) < 2 and i < len(all_feedback_requests_and_genres) - 1:
                    all_genres_valid = False
                    self.merge_genres(
                        all_feedback_requests_and_genres,
                        i,
                        i + 1
                    )
                    break

        # Sort by reverse length so genres with more requests are grouped first.
        all_feedback_requests_and_genres = sorted(
            all_feedback_requests_and_genres,
            key=lambda requests_and_genres: -len(requests_and_genres[0]),
        )

        feedback_groups = []
        for feedback_requests, genres in all_feedback_requests_and_genres:
            # Sort genres alphabetically for naming consistency.
            groups_for_genres = self.assign_groups_for_requests(
                feedback_requests=feedback_requests,
                genres=sorted(list(genres), key=lambda genre: genre.value)
            )
            feedback_groups += groups_for_genres

        # Distribute trackless requests across existing groups,
        # priortising small groups before ratings.
        # Cast to a list to allow us to remove requests later as they are assigned.
        unassigned_feedback_requests_without_tracks = list(FeedbackRequest.objects.filter(
            feedback_group=None,
            media_url__isnull=True,
        ).order_by(
            '-user__rating',
        ).all())

        # Prioritise groups with < 4 requests to make sure everyone gets as many
        # feedback responses as possible.
        feedback_groups = sorted(
            feedback_groups,
            key=lambda feedback_group_tuple: (
                feedback_group_tuple[0].feedback_requests.count(),
            )
        )

        feedback_group_index = 0
        while len(unassigned_feedback_requests_without_tracks) > 0:
            for feedback_request in unassigned_feedback_requests_without_tracks:
                if feedback_group_index >= len(feedback_groups):
                    feedback_group_index = 0
                feedback_group, genres = feedback_groups[feedback_group_index]
                if GenreChoice[feedback_request.genre] in genres:
                    feedback_request.feedback_group = feedback_group

                    # Add response forms for the other requests in the group that aren't trackless.
                    other_feedback_requests_with_tracks = feedback_group.feedback_requests.filter(
                        media_url__isnull=False,
                    ).exclude(
                        id=feedback_request.id,
                    ).all()
                    for other_feedback_request in other_feedback_requests_with_tracks:
                        feedback_response = FeedbackResponse(
                            feedback_request=other_feedback_request,
                            user=feedback_request.user,
                        )
                        feedback_response.save()

                    feedback_request.save()

                    self.send_email_to_group_member(
                        email=feedback_request.user.email,
                        feedback_group_name=feedback_group.name,
                        feedback_group_url=WEBSITE_URL.format(
                            path=f'/group/{feedback_group.id}'
                        ),
                        is_trackless=True,
                    )

                    unassigned_feedback_requests_without_tracks.remove(feedback_request)
                    feedback_group_index += 1
            feedback_group_index += 1




