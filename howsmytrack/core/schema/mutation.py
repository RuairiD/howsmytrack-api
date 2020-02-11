import datetime

import graphene
import graphql_jwt
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db import transaction
from django.utils import timezone

from graphene_django.types import DjangoObjectType

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import MediaTypeChoice


INVALID_MEDIA_URL_MESSAGE = 'Please provide any of the following: a valid Soundcloud URL of the form `https://soundcloud.com/artist/track` (or `https://soundcloud.com/artist/track/secret` for private tracks), a shareable Google Drive URL of the form `https://drive.google.com/file/d/abcdefghijklmnopqrstuvwxyz1234567/view` or a Dropbox URL of the form `https://www.dropbox.com/s/abcdefghijklmno/filename`'


INVALID_PASSWORD_MESSAGE = 'Please choose a more secure password. Your password must contain at least 8 characters, can’t be a commonly used password (e.g. "password") and can’t be entirely numeric.'


class RefreshTokenFromCookie(graphql_jwt.Refresh):
    """
    The built-in graphql_jwt.Refresh mutation requires the token to be passed as
    a parameter. This custom mutation reads the token from HttpOnly cookies
    instead to prevent frontends having to store the cookie somewhere else for access.
    """
    class Arguments:
        pass

    @classmethod
    def mutate(cls, *args, **kwargs):
        cookies = args[1].context.COOKIES
        if cookies and 'JWT' in cookies:
            kwargs['token'] = cookies['JWT']
            return super(RefreshTokenFromCookie, cls).mutate(
                *args,
                **kwargs,
            )
        # If no token cookie exists, nothing to do.
        return None


class RegisterUser(graphene.Mutation):

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        password_repeat = graphene.String(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, email, password, password_repeat):
        validator = EmailValidator()
        try:
            validator(email)
        except ValidationError:
            return RegisterUser(success=False, error="Please provide a valid email address.")

        if password == password_repeat:
            try:
                validate_password(password)
            except ValidationError as e:
                return RegisterUser(success=False, error=INVALID_PASSWORD_MESSAGE)

            try:
                with transaction.atomic():
                    user = FeedbackGroupsUser.create(
                        email=email,
                        password=password
                    )
                    user.save()
                    return RegisterUser(success=bool(user.id))
            except IntegrityError:
                return RegisterUser(success=False, error="An account for that email address already exists.")
        return RegisterUser(success=False, error="Passwords don't match.")


def validate_media_url(media_url):
    url_validator = URLValidator()
    try:
        url_validator(media_url)
    except ValidationError:
        raise ValidationError(
            message=INVALID_MEDIA_URL_MESSAGE,
        )
    if 'https://soundcloud.com/' in media_url:
        return MediaTypeChoice.SOUNDCLOUD.name
    if 'dropbox.com/' in media_url:
        return MediaTypeChoice.DROPBOX.name
    if 'drive.google.com/file' in media_url:
        return MediaTypeChoice.GOOGLEDRIVE.name
    raise ValidationError(
        message=INVALID_MEDIA_URL_MESSAGE,
    )

class CreateFeedbackRequest(graphene.Mutation):

    class Arguments:
        media_url = graphene.String(required=True)
        feedback_prompt = graphene.String(required=False)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, media_url, feedback_prompt=None):
        user = info.context.user
        if user.is_anonymous:
            return CreateFeedbackRequest(
                success=False,
                error='Not logged in.',
            )

        # Validate the media url
        media_type = None
        try:
            media_type = validate_media_url(media_url)
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
            media_url=media_url,
            feedback_group=None,
        ).count()
        if existing_track_requests > 0:
            return CreateFeedbackRequest(
                success=False,
                error='A request for this track is already pending.',
            )
        
        feedback_request = FeedbackRequest(
            user=feedback_groups_user,
            media_url=media_url,
            media_type=media_type,
            feedback_prompt=feedback_prompt,
        )
        feedback_request.save()

        return CreateFeedbackRequest(success=True, error=None)


class EditFeedbackRequest(graphene.Mutation):

    class Arguments:
        feedback_request_id = graphene.Int(required=True)
        media_url = graphene.String(required=False)
        feedback_prompt = graphene.String(required=False)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, feedback_request_id, media_url, feedback_prompt=None):
        user = info.context.user
        if user.is_anonymous:
            return EditFeedbackRequest(
                success=False,
                error='Not logged in.',
            )

        # Validate the media url
        media_type = None
        try:
            media_type = validate_media_url(media_url)
        except ValidationError as e:
            return EditFeedbackRequest(
                success=False,
                error=e.message,
            )

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
    
        # Reject the edit if the user does not own the request (or if it doesn't exist)
        feedback_request = FeedbackRequest.objects.filter(
            user=feedback_groups_user,
            id=feedback_request_id,
        ).first()
        if not feedback_request:
            return EditFeedbackRequest(
                success=False,
                error='You are not the owner of this feedback request.',
            )

        # Reject the edit if the request has already been assigned to a group.
        if feedback_request.feedback_group:
            return EditFeedbackRequest(
                success=False,
                error='This request has already been assigned to a feedback group and cannot be edited.',
            )
        
        if media_url:
            feedback_request.media_url = media_url
            feedback_request.media_type = media_type
        # Allow empty feedback prompt
        if feedback_prompt is not None:
            feedback_request.feedback_prompt = feedback_prompt
        feedback_request.save()

        return EditFeedbackRequest(success=True, error=None)


class SubmitFeedbackResponse(graphene.Mutation):

    class Arguments:
        feedback_response_id = graphene.Int(required=True)
        feedback = graphene.String(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, feedback_response_id, feedback):
        user = info.context.user
        if user.is_anonymous:
            return SubmitFeedbackResponse(success=False, error='Not logged in.')

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
        
        feedback_response = FeedbackResponse.objects.filter(
            user=feedback_groups_user,
            id=feedback_response_id,
        ).first()

        if not feedback_response:
            return SubmitFeedbackResponse(success=False, error='Invalid feedback_response_id')

        if feedback_response.submitted:
            return SubmitFeedbackResponse(success=False, error='Feedback has already been submitted')

        feedback_response.feedback = feedback
        feedback_response.time_submitted = timezone.now()
        feedback_response.submitted = True
        feedback_response.save()

        return SubmitFeedbackResponse(success=True, error=None)


class RateFeedbackResponse(graphene.Mutation):

    class Arguments:
        feedback_response_id = graphene.Int(required=True)
        rating = graphene.Int(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, feedback_response_id, rating):
        user = info.context.user
        if user.is_anonymous:
            return RateFeedbackResponse(success=False, error='Not logged in.')

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
        
        feedback_response = FeedbackResponse.objects.filter(
            feedback_request__user=feedback_groups_user,
            id=feedback_response_id,
        ).first()

        if not feedback_response:
            return RateFeedbackResponse(success=False, error='Invalid feedback_response_id')

        if not feedback_response.submitted:
            return RateFeedbackResponse(success=False, error='This feedback has not been submitted and cannot be rated.')

        if feedback_response.rating:
            return RateFeedbackResponse(success=False, error='Feedback has already been rated')

        if rating < 1 or rating > 5:
            return RateFeedbackResponse(success=False, error='Invalid rating')

        feedback_response.rating = rating
        feedback_response.save()

        return RateFeedbackResponse(success=True, error=None)


class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    create_feedback_request = CreateFeedbackRequest.Field()
    edit_feedback_request = EditFeedbackRequest.Field()
    submit_feedback_response = SubmitFeedbackResponse.Field()
    rate_feedback_response = RateFeedbackResponse.Field()
    refresh_token_from_cookie = RefreshTokenFromCookie.Field()
