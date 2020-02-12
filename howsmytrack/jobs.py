from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.jobstores import register_events
from django_apscheduler.jobstores import register_job
from django.core.management import call_command
from django.utils import timezone


scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

# 10 AM UTC; focusing on Americans who get their groups assigned while they sleep.
JOB_HOUR = 10

# Lock is used to prevent the same job running multiple times simultaneously. In the long term,
# I would prefer to figure out why this is happening, even with just one instance running.
lock = Lock()


@register_job(scheduler, 'cron', hour=JOB_HOUR)
def calculate_user_ratings():
    with lock:
        print('Starting: calculate_user_ratings')
        call_command('calculate_user_ratings')
        print('Done: calculate_user_ratings')


@register_job(scheduler, 'cron', hour=JOB_HOUR, minute=30)
def assign_groups():
    with lock:
        print('Starting: assign_groups')
        call_command('assign_groups')
        print('Done: assign_groups')


def start_scheduler():
    with lock:
        if scheduler.state == 0:
            register_events(scheduler)
            scheduler.start()
            print('Started scheduler.')
        else:
            print('Attempted to start scheduler, but scheduler was already running.')
