# Generated by Django 3.0.2 on 2020-02-16 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20200216_0921'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackrequest',
            name='reminder_email_sent',
            field=models.BooleanField(default=False),
        ),
    ]