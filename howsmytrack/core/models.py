from enum import Enum

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator


class FeedbackGroupsUser(models.Model):
    """
    Composition of basic User class to include ratings.

    When doing any sort of interaction involving users, *this* is the model
    that should be used; *not* django.contrib.auth.models.User
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rating = models.FloatField(default=0)

    @classmethod
    def create(cls, email, password):
        user = User.objects.create_user(
            username=email,
            password=password,
            email=email,
        )
        user.save()
        return FeedbackGroupsUser(user=user)

    @property
    def email(self):
        return self.user.email

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'FeedbackGroupsUser'
        verbose_name_plural = 'FeedbackGroupsUsers'


class FeedbackGroup(models.Model):
    name = models.CharField(max_length=100)
    time_created = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.name} ({self.time_created})'

    class Meta:
        verbose_name = 'FeedbackGroup'
        verbose_name_plural = 'FeedbackGroups'


class MediaTypeChoice(Enum):
    SOUNDCLOUD = 'Soundcloud'
    GOOGLEDRIVE = 'Google Drive'
    DROPBOX = 'Dropbox'


class FeedbackRequest(models.Model):
    """
    A request for feedback submitted by a user.
    """
    user = models.ForeignKey(
        FeedbackGroupsUser,
        related_name='feedback_requests',
        on_delete=models.CASCADE
    )
    media_url = models.CharField(max_length=100)
    media_type = models.CharField(
        max_length=32,
        choices=[(tag.name, tag.value) for tag in MediaTypeChoice],
    )
    feedback_prompt = models.TextField(
        blank=True,
        null=True,
    )
    feedback_group = models.ForeignKey(
        FeedbackGroup,
        related_name='feedback_requests',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    time_created = models.DateTimeField(auto_now_add=True)
    email_when_grouped = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user}\'s request for {self.media_url} ({self.time_created})'

    class Meta:
        verbose_name = 'FeedbackRequest'
        verbose_name_plural = 'FeedbackRequests'


class FeedbackResponse(models.Model):
    """
    A response to a FeedbackRequest.
    
    When requests are assigned groups in `assign_groups`, blank
    FeedbackResponses are created for every user-request pairing
    (except responses for a user's own request).

    Responses are allowed to sit empty in the database but users will
    not be able to see their own feedback until they have left it for
    everyone else.
    """
    feedback_request = models.ForeignKey(
        FeedbackRequest,
        related_name='feedback_responses',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        FeedbackGroupsUser,
        related_name='feedback_responses',
        on_delete=models.CASCADE
    )
    feedback = models.TextField(
        blank=True,
        null=True,
    )
    time_submitted = models.DateTimeField(
        blank=True,
        null=True,
    )
    submitted = models.BooleanField(default=False)
    rating = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    def __str__(self):
        return f'{self.user} responded: "{self.feedback}" to {self.feedback_request}'

    class Meta:
        verbose_name = 'FeedbackResponse'
        verbose_name_plural = 'FeedbackResponses'
