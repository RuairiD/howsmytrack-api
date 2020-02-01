# Generated by Django 3.0.2 on 2020-01-31 21:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('feedbackgroups', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedbackrequest',
            name='feedback_group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='feedback_requests', to='feedbackgroups.FeedbackGroup'),
        ),
    ]
