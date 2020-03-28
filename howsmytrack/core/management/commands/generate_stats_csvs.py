import csv

from django.core.management.base import BaseCommand

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse


DATE_STRING = '{day}/{month}/{year}'
DATETIME_STRING = '{day}/{month}/{year} {hour}:{minute}:{second}'


def format_datetime(date):
    return DATETIME_STRING.format(
        day=date.day,
        month=date.month,
        year=date.year,
        hour=date.hour,
        minute=date.minute,
        second=date.second,
    )


def format_date(date):
    return DATE_STRING.format(
        day=date.day,
        month=date.month,
        year=date.year,
    )


def format_feedback_request(feedback_request, count):
    return format_datetime(feedback_request.time_created), count


def format_feedback_groups_user(feedback_groups_user, count):
    return format_datetime(feedback_groups_user.user.date_joined), count


def build_feedback_requests():
    with open('feedback_requests.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        feedback_requests = FeedbackRequest.objects.all()

        feedback_request_count = 0
        for feedback_request in feedback_requests:
            feedback_request_count += 1
            writer.writerow(
                format_feedback_request(
                    feedback_request,
                    feedback_request_count,
                )
            )


def build_feedback_groups_users():
    with open('feedback_groups_users.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        feedback_groups_users = FeedbackGroupsUser.objects.all()

        feedback_groups_user_count = 0
        for feedback_groups_user in feedback_groups_users:
            feedback_groups_user_count += 1
            writer.writerow(
                format_feedback_groups_user(
                    feedback_groups_user,
                    feedback_groups_user_count,
                )
            )


def build_response_rates_by_date():
    with open('feedback_response_rates.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        feedback_responses = FeedbackResponse.objects.all()

        feedback_responses_by_date = {}
        for feedback_response in feedback_responses:
            time_created = format_date(
                feedback_response.feedback_request.feedback_group.time_created,
            )
            if time_created not in feedback_responses_by_date:
                feedback_responses_by_date[time_created] = []

            feedback_responses_by_date[time_created].append(feedback_response)

        for date in feedback_responses_by_date:
            feedback_responses = feedback_responses_by_date[date]
            submissions = 0
            for feedback_response in feedback_responses:
                if feedback_response.submitted:
                    submissions += 1
            writer.writerow(
                (date, submissions / len(feedback_responses))
            )


def build_feedback_requests_by_date():
    with open('feedback_requests_by_date.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        feedback_requests = FeedbackRequest.objects.all()

        feedback_requests_by_date = {}
        for feedback_request in feedback_requests:
            time_created = format_date(
                feedback_request.time_created,
            )
            if time_created not in feedback_requests_by_date:
                feedback_requests_by_date[time_created] = []

            feedback_requests_by_date[time_created].append(feedback_request)

        for date in feedback_requests_by_date:
            feedback_requests = feedback_requests_by_date[date]
            writer.writerow(
                (date, len(feedback_requests))
            )


def build_feedback_groups_users_by_date():
    with open('feedback_groups_users_by_date.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        feedback_groups_users = FeedbackGroupsUser.objects.all()

        feedback_groups_users_by_date = {}
        for feedback_groups_user in feedback_groups_users:
            time_created = format_date(
                feedback_groups_user.user.date_joined
            )
            if time_created not in feedback_groups_users_by_date:
                feedback_groups_users_by_date[time_created] = []

            feedback_groups_users_by_date[time_created].append(feedback_groups_user)

        for date in feedback_groups_users_by_date:
            feedback_groups_users = feedback_groups_users_by_date[date]
            writer.writerow(
                (date, len(feedback_groups_users))
            )


class Command(BaseCommand):
    """
    To be run locally, not on prod (therefore untested).

    Get a local copy of the proddb with:
    rm db.sqlite3 && heroku run --app howsmytrack-api python manage.py dumpdata | tail -n 1  > proddb.json && python manage.py migrate &&  python manage.py loaddata proddb.json
    """
    help = 'Generate CSV files with usage stats'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        build_feedback_requests()
        build_feedback_groups_users()
        build_response_rates_by_date()
        build_feedback_requests_by_date()
        build_feedback_groups_users_by_date()
