from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management import call_command

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour=0)
def assign_groups():
    call_command('assign_groups')

@sched.scheduled_job('cron', hour=0)
def calculate_user_ratings():
    call_command('calculate_user_ratings')

sched.start()
