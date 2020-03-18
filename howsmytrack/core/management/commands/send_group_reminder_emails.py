from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.template.loader import render_to_string
from django.utils import timezone

from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse

MIN_GROUP_AGE = timedelta(hours=20)

WEBSITE_URL = 'https://www.howsmytrack.com{path}'

class Command(BaseCommand):
    """
    Send a reminder email to all users with assigned requests who:
        - have incomplete feedback
        - have emails enabled for the request
        - have not already received a reminder email
        - are members of a group that has existed for >20hrs
    """
    help = 'Sends reminder emails for all assigned requests with enabled emails'

    def add_arguments(self, parser):
        pass

    def send_reminder_email_for_request(self, feedback_request):
        if feedback_request.media_url is not None:
            message = render_to_string('group_reminder_email.txt', {
                'email': feedback_request.user.email,
                'feedback_group_name': feedback_request.feedback_group.name,
                'feedback_group_url': WEBSITE_URL.format(
                    path=f'/group/{feedback_request.feedback_group.id}'
                ),
            })
            html_message = render_to_string('group_reminder_email.html', {
                'email': feedback_request.user.email,
                'feedback_group_name': feedback_request.feedback_group.name,
                'feedback_group_url': WEBSITE_URL.format(
                    path=f'/group/{feedback_request.feedback_group.id}'
                ),
            })
        else:
            message = render_to_string('group_reminder_email_trackless.txt', {
                'email': feedback_request.user.email,
                'feedback_group_name': feedback_request.feedback_group.name,
                'feedback_group_url': WEBSITE_URL.format(
                    path=f'/group/{feedback_request.feedback_group.id}'
                ),
            })
            html_message = render_to_string('group_reminder_email_trackless.html', {
                'email': feedback_request.user.email,
                'feedback_group_name': feedback_request.feedback_group.name,
                'feedback_group_url': WEBSITE_URL.format(
                    path=f'/group/{feedback_request.feedback_group.id}'
                ),
            })

        send_mail(
            subject="don't forget your feedback group!",
            message=message,
            from_email=None, # Use default in settings.py
            recipient_list=[feedback_request.user.email],
            html_message=html_message,
        )

        feedback_request.reminder_email_sent = True
        feedback_request.save()

    def handle(self, *args, **options):
        max_group_time_created = timezone.now() - MIN_GROUP_AGE
        unreminded_feedback_requests = FeedbackRequest.objects.filter(
            feedback_group__isnull=False,
            feedback_group__time_created__lt=max_group_time_created,
            email_when_grouped=True,
            reminder_email_sent=False,
            # Don't send reminder emails to users who have disabled them.
            user__send_reminder_emails=True,
        ).all()

        for feedback_request in unreminded_feedback_requests:
            # Only send reminder for users who have unsubmitted responses for the group.
            incomplete_responses_for_user = FeedbackResponse.objects.filter(
                feedback_request__feedback_group=feedback_request.feedback_group,
                user=feedback_request.user,
                submitted=False,
            ).count()
            if incomplete_responses_for_user > 0:
                self.send_reminder_email_for_request(feedback_request)
