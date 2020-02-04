import datetime

import graphene
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.utils import timezone

from graphene_django.types import DjangoObjectType

from feedbackgroups.feedbackgroups.models import FeedbackGroupsUser
from feedbackgroups.feedbackgroups.models import FeedbackGroup
from feedbackgroups.feedbackgroups.models import FeedbackRequest
from feedbackgroups.feedbackgroups.models import FeedbackResponse


INVALID_SOUNDCLOUD_URL_MESSAGE = 'Please provide a valid Soundcloud URL of the form `https://soundcloud.com/artist/track` (or `https://soundcloud.com/artist/track/secret` for private tracks).'


class FeedbackRequestType(DjangoObjectType):
    class Meta:
        model = FeedbackRequest


class FeedbackResponseType(DjangoObjectType):
    class Meta:
        model = FeedbackResponse


class UserType(graphene.ObjectType):
    username = graphene.String()
    rating = graphene.Float()


class FeedbackGroupType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    soundcloud_url = graphene.String()
    members = graphene.Int()
    # User's feedback responses for other group member's requests 
    feedback_responses = graphene.List(FeedbackResponseType)
    # Feedback received by the user; only sent once user has completed all feedbackReponses
    user_feedback_responses = graphene.List(FeedbackResponseType)


class RegisterUser(graphene.Mutation):

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        password_repeat = graphene.String(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def mutate(self, info, email, password, password_repeat):
        validator = EmailValidator()
        try:
            validator(email)
        except ValidationError:
            return RegisterUser(success=False, error="Please provide a valid email address.")

        if password == password_repeat:
            try:
                user = FeedbackGroupsUser.create(
                    email=email,
                    password=password
                )
                user.save()
                return RegisterUser(success=bool(user.id))
            except IntegrityError:
                return RegisterUser(success=False, error="An account for that email address already exists.")
        return RegisterUser(success=False, error="Passwords don't match.")


def validate_soundcloud_url(soundcloud_url):
    url_validator = URLValidator()
    try:
        url_validator(soundcloud_url)
    except ValidationError:
        raise ValidationError(
            message=INVALID_SOUNDCLOUD_URL_MESSAGE,
        )
    if 'https://soundcloud.com/' not in soundcloud_url:
        raise ValidationError(
            message=INVALID_SOUNDCLOUD_URL_MESSAGE,
        )

class CreateFeedbackRequest(graphene.Mutation):

    class Arguments:
        soundcloud_url = graphene.String(required=True)
        feedback_prompt = graphene.String(required=False)

    success = graphene.Boolean()
    error = graphene.String()

    def mutate(self, info, soundcloud_url, feedback_prompt=None):
        user = info.context.user
        if user.is_anonymous:
            return CreateFeedbackRequest(
                success=False,
                error='Not logged in.',
            )

        # Validate the soundcloud url
        try:
            validate_soundcloud_url(soundcloud_url)
        except ValidationError as e:
            return CreateFeedbackRequest(
                success=False,
                error=e.message,
            )

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
    
        # Only create a new request if the user has an outstanding, ungrouped request
        # (should only happen if user's request is from within the last 24 hours or
        # the request is the only one submitted :cry: )
        unassigned_requests = FeedbackRequest.objects.filter(
            user=feedback_groups_user,
            feedback_group=None,
        ).count()
        if unassigned_requests > 0:
            return CreateFeedbackRequest(
                success=False,
                error='You have an unassigned feedback request. Once that request has been assigned to a feedback group, you will be eligible to submit another request.',
            )

        # Reject requests for the same URL (if the other submission hasn't been grouped yet)
        # This prevents users creating multiple accounts to request the same track.
        existing_track_requests = FeedbackRequest.objects.filter(
            soundcloud_url=soundcloud_url,
            feedback_group=None,
        ).count()
        if existing_track_requests > 0:
            return CreateFeedbackRequest(
                success=False,
                error='A request for this track is already pending.',
            )
        
        feedback_request = FeedbackRequest(
            user=feedback_groups_user,
            soundcloud_url=soundcloud_url,
            feedback_prompt=feedback_prompt,
        )
        feedback_request.save()

        return CreateFeedbackRequest(success=True, error=None)


class SaveFeedbackResponse(graphene.Mutation):

    class Arguments:
        feedback_response_id = graphene.Int(required=True)
        feedback = graphene.String(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, feedback_response_id, feedback):
        user = info.context.user
        if user.is_anonymous:
            return SaveFeedbackResponse(success=False, errors=['Not logged in'])

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
        
        feedback_response = FeedbackResponse.objects.filter(
            user=feedback_groups_user,
            id=feedback_response_id,
        ).first()

        if not feedback_response:
            return SaveFeedbackResponse(success=False, errors=['Invalid feedback_response_id'])

        if feedback_response.submitted:
            return SaveFeedbackResponse(success=False, errors=['Feedback has already been submitted'])

        feedback_response.feedback = feedback
        feedback_response.save()

        return CreateFeedbackRequest(success=True, errors=None)


class SubmitFeedbackResponse(graphene.Mutation):

    class Arguments:
        feedback_response_id = graphene.Int(required=True)
        feedback = graphene.String(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def mutate(self, info, feedback_response_id, feedback):
        user = info.context.user
        if user.is_anonymous:
            return SaveFeedbackResponse(success=False, error='Not logged in')

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
        
        feedback_response = FeedbackResponse.objects.filter(
            user=feedback_groups_user,
            id=feedback_response_id,
        ).first()

        if not feedback_response:
            return SaveFeedbackResponse(success=False, error='Invalid feedback_response_id')

        if feedback_response.submitted:
            return SaveFeedbackResponse(success=False, error='Feedback has already been submitted')

        feedback_response.feedback = feedback
        feedback_response.time_submitted = timezone.now()
        feedback_response.submitted = True
        feedback_response.save()

        return CreateFeedbackRequest(success=True, error=None)


class RateFeedbackResponse(graphene.Mutation):

    class Arguments:
        feedback_response_id = graphene.Int(required=True)
        rating = graphene.Int(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def mutate(self, info, feedback_response_id, rating):
        user = info.context.user
        if user.is_anonymous:
            return SaveFeedbackResponse(success=False, error='Not logged in')

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
        
        feedback_response = FeedbackResponse.objects.filter(
            feedback_request__user=feedback_groups_user,
            id=feedback_response_id,
        ).first()

        if not feedback_response:
            return SaveFeedbackResponse(success=False, error='Invalid feedback_response_id')

        if feedback_response.rating:
            return SaveFeedbackResponse(success=False, error='Feedback has already been rated')

        feedback_response.rating = rating
        feedback_response.save()

        return CreateFeedbackRequest(success=True, error=None)


def format_feedback_group(feedback_group, feedback_groups_user):
    user_feedback_request = [
        feedback_request
        for feedback_request in feedback_group.feedback_requests.all()
        if feedback_request.user == feedback_groups_user
    ][0]

    feedback_requests_for_user = [
        feedback_request
        for feedback_request in feedback_group.feedback_requests.all()
        if feedback_request.user != feedback_groups_user
    ]

    feedback_responses = set()
    for feedback_request in feedback_requests_for_user:
        for feedback_response in feedback_request.feedback_responses.all():
            if feedback_response.user == feedback_groups_user:
                feedback_responses.add(feedback_response)

    # If user has responded to all requests, find user's request and get responses
    user_feedback_responses = None
    if all([feedback_response.submitted for feedback_response in feedback_responses]):
        # Only returned submitted responses
        user_feedback_responses = user_feedback_request.feedback_responses.filter(
            submitted=True,
        ).all()

    return FeedbackGroupType(
        id=feedback_group.id,
        name=feedback_group.name,
        soundcloud_url=user_feedback_request.soundcloud_url,
        members=feedback_group.feedback_requests.count(),
        feedback_responses=feedback_responses,
        user_feedback_responses=user_feedback_responses,
    )


class Query(graphene.ObjectType):
    user_details = graphene.Field(UserType)

    feedback_group = graphene.Field(
        FeedbackGroupType,
        feedback_group_id=graphene.Int(required=True),
    )
    feedback_groups = graphene.List(FeedbackGroupType)

    def resolve_user_details(self, info):
        user = info.context.user
        if user.is_anonymous:
            return None

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        # Only show user rating if a rating has been assigned
        rating = None
        if feedback_groups_user.rating:
            rating = feedback_groups_user.rating

        return UserType(
            username=user.username,
            rating=rating,
        )

    def resolve_feedback_group(self, info, feedback_group_id):
        user = info.context.user
        if user.is_anonymous:
            return None
        
        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        feedback_group =  FeedbackGroup.objects.filter(
            id=feedback_group_id,
        ).first()

        return format_feedback_group(feedback_group, feedback_groups_user)


    def resolve_feedback_groups(self, info):
        user = info.context.user
        if user.is_anonymous:
            return []
        
        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        feedback_requests = FeedbackRequest.objects.filter(
            user=feedback_groups_user,
        ).order_by(
            '-time_created'
        ).all()

        return [
            format_feedback_group(feedback_request.feedback_group, feedback_groups_user)
            for feedback_request in feedback_requests
            if feedback_request.feedback_group
        ]


class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    create_feedback_request = CreateFeedbackRequest.Field()
    save_feedback_response = SaveFeedbackResponse.Field()
    submit_feedback_response = SubmitFeedbackResponse.Field()
    rate_feedback_response = RateFeedbackResponse.Field()
