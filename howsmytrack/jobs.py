from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.jobstores import register_events
from django_apscheduler.jobstores import register_job
from django.core.management import call_command


scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

# 2 AM UTC; Americans get groups in the evenings, Europeans can have them in the morning.
JOB_HOUR = 2


@register_job(scheduler, 'cron', hour=JOB_HOUR)
def assign_groups():
    print('Starting: assign_groups')
    call_command('assign_groups')
    print('Done: assign_groups')


@register_job(scheduler, 'cron', hour=JOB_HOUR)
def calculate_user_ratings():
    print('Starting: calculate_user_ratings')
    call_command('calculate_user_ratings')
    print('Done: calculate_user_ratings')


register_events(scheduler)

scheduler.start()
print('Started scheduler.')
