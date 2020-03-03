# Generated by Django 3.0.3 on 2020-03-03 01:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_feedbackrequest_genre'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedbackrequest',
            name='genre',
            field=models.CharField(blank=True, choices=[('ELECTRONIC', 'Electronic'), ('HIPHOP', 'Hip-Hop/Rap'), ('NO_GENRE', 'No Genre')], default='NO_GENRE', max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='feedbackrequest',
            name='media_type',
            field=models.CharField(blank=True, choices=[('SOUNDCLOUD', 'Soundcloud'), ('GOOGLEDRIVE', 'Google Drive'), ('DROPBOX', 'Dropbox'), ('ONEDRIVE', 'OneDrive')], max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='feedbackrequest',
            name='media_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
