from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator


class FeedbackGroupsUser(models.Model):
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

    def __str__(self):
        return self.user.username


class FeedbackGroup(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class FeedbackRequest(models.Model):
    user = models.ForeignKey(
        FeedbackGroupsUser,
        related_name='feedback_requests',
        on_delete=models.CASCADE
    )
    soundcloud_url = models.CharField(max_length=100)
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

    def __str__(self):
        return f'{self.user}\'s request for {self.soundcloud_url}'


class FeedbackResponse(models.Model):
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
