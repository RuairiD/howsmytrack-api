from enum import Enum

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator


MAX_DISPLAY_STRING_LENGTH = 50
def truncate_string(string, length=MAX_DISPLAY_STRING_LENGTH):
    if len(string) > length:
        return string[:length] + '…'
    return string


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
    name = models.CharField(max_length=255)
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
    ONEDRIVE = 'OneDrive'


class GenreChoice(Enum):
    ELECTRONIC = 'Electronic'
    HIPHOP = 'Hip-Hop/Rap'
    NO_GENRE = 'No Genre'


class FeedbackRequest(models.Model):
    """
    A request to join a feedback group submitted by the user. If the user
    provides a `media_url`, the request will be added to a group and the user
    can both provide feedback for others and receive feedback for their own.
    If the user does *not* provide a `media_url`, the request can still be
    added to a group but the user will not receive any feedback, although they
    can still provide it.
    """
    user = models.ForeignKey(
        FeedbackGroupsUser,
        related_name='feedback_requests',
        on_delete=models.CASCADE
    )
    media_url = models.CharField(
        max_length=255,
        # If this field is empty, the request is considered to be 'trackless'
        # and the user will be added to a group to give feedback but will not
        # receive any feedback.
        blank=True,
        null=True,
    )
    media_type = models.CharField(
        max_length=32,
        choices=[(tag.name, tag.value) for tag in MediaTypeChoice],
        blank=True,
        null=True,
    )
    feedback_prompt = models.TextField(
        blank=True,
        null=True,
    )
    genre = models.CharField(
        max_length=32,
        choices=[(tag.name, tag.value) for tag in GenreChoice],
        default=GenreChoice.NO_GENRE.name,
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
    reminder_email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user}\'s request for {truncate_string(self.media_url)} ({self.time_created})'

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
    allow_replies = models.BooleanField(default=False)
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

    @property
    def ordered_replies(self):
        return self.replies.order_by(
            'time_created'
        ).all()

    @property
    def allow_further_replies(self):
        return FeedbackResponseReply.objects.filter(
            feedback_response=self,
            allow_replies=False,
        ).count() == 0

    def __str__(self):
        return f'{self.user} responded: "{truncate_string(self.feedback)}" to {self.feedback_request}'

    class Meta:
        verbose_name = 'FeedbackResponse'
        verbose_name_plural = 'FeedbackResponses'


class FeedbackResponseReply(models.Model):
    """
    A reply to a FeedbackResponse.
    
    TODO: write more here please
    """
    feedback_response = models.ForeignKey(
        FeedbackResponse,
        related_name='replies',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        FeedbackGroupsUser,
        related_name='replies',
        on_delete=models.CASCADE
    )
    text = models.TextField()
    allow_replies = models.BooleanField(default=True)
    time_created = models.DateTimeField(auto_now_add=True)
    time_read = models.DateTimeField(
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.user} replied: "{truncate_string(self.text)}"'

    class Meta:
        verbose_name = 'FeedbackResponseReply'
        verbose_name_plural = 'FeedbackResponseReplies'
