import datetime

import graphene
import graphql_jwt
from django.contrib.auth.models import User
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
from howsmytrack.core.models import FeedbackResponseReply
from howsmytrack.core.models import MediaTypeChoice


# TODO specific error messages for each supported platform, including instructions on how to obtain the correct links.
# Part of this can be achieved by passing back an `invalid_media_url` field which, when true, causes the client to show
# formatted instructions and perhaps an informational modal.
INVALID_MEDIA_URL_MESSAGE = 'Please provide any of the following: a valid Soundcloud URL of the form `https://soundcloud.com/artist/track` (or `https://soundcloud.com/artist/track/secret` for private tracks), a shareable Google Drive URL of the form `https://drive.google.com/file/d/abcdefghijklmnopqrstuvwxyz1234567/view`, a Dropbox URL of the form `https://www.dropbox.com/s/abcdefghijklmno/filename` or a OneDrive URL of the form `https://onedrive.live.com/?authkey=AUTHKEY&cid=CID&id=ID`'


INVALID_PASSWORD_MESSAGE = 'Please choose a more secure password. Your password must contain at least 8 characters, can’t be a commonly used password (e.g. "password") and can’t be entirely numeric.'


ONEDRIVE_DOWNLOAD_PARTS = [
    'https://onedrive.live.com/download',
    'authkey=',
    'cid=',
    'resid=',
]
ONEDRIVE_FILE_PARTS = [
    'https://onedrive.live.com/',
    'authkey=',
    'cid=',
    'id=',
]


class ObtainJSONWebTokenCaseInsensitive(graphql_jwt.ObtainJSONWebToken):
    """
    Retain all functionality of graphql_jwt.ObtainJSONWebToken but check if
    a user exists with the username in another case. If one exists, pass
    through the correct username instead.

    However, since some accounts were already created before this changed with
    the same email in multiple cases, we're allowing those accounts to
    persist by logging them in using the exact email address with exact casing.

    e.g.
        - if the user has the username 'davy@gmail.com', an attempt to log in
          with 'DAVY@gmail.com' will be accepted.
        - if the user has the username 'davy@gmail.com' and another has 'Davy@gmail.com',
          an attempt to log in with 'DAVY@gmail.com' will be accepted for whichever
          account was created first, while using the exact emails will guarantee
          the exact account.
    """
    class Arguments:
        pass

    @classmethod
    def mutate(cls, *args, **kwargs):
        exact_user = User.objects.filter(username=kwargs['username']).first()
        different_case_user = User.objects.filter(username__iexact=kwargs['username']).first()
        if not exact_user and different_case_user:
            kwargs['username'] = different_case_user.username
        return super(ObtainJSONWebTokenCaseInsensitive, cls).mutate(
            *args,
            **kwargs,
        )


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

        # Don't allow users to sign up with the same email in a different case.
        existing_users = User.objects.filter(username__iexact=email).count()
        if existing_users > 0:
            return RegisterUser(success=False, error="An account for that email address already exists.")

        if password == password_repeat:
            try:
                validate_password(password)
            except ValidationError as e:
                return RegisterUser(success=False, error=INVALID_PASSWORD_MESSAGE)

            with transaction.atomic():
                user = FeedbackGroupsUser.create(
                    email=email,
                    password=password
                )
                user.save()
                return RegisterUser(success=bool(user.id))
        return RegisterUser(success=False, error="Passwords don't match.")


def is_onedrive_url(media_url):
    # Directly downloadable URLs are used for OneDrive links.
    # If the user provides this directly, great. Otherwise, we can
    # still assemble the link from the regular file URL.
    # We cannot do anything with a OneDrive shortlink from the
    # Share menu and should reject it.
    return all([
        url_part in media_url
        for url_part in ONEDRIVE_DOWNLOAD_PARTS
    ]) or all([
        url_part in media_url
        for url_part in ONEDRIVE_FILE_PARTS
    ])


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
    if is_onedrive_url(media_url):
        return MediaTypeChoice.ONEDRIVE.name
    raise ValidationError(
        message=INVALID_MEDIA_URL_MESSAGE,
    )

class CreateFeedbackRequest(graphene.Mutation):

    class Arguments:
        media_url = graphene.String(required=False)
        genre = graphene.String(required=False)
        email_when_grouped = graphene.Boolean(required=False)
        feedback_prompt = graphene.String(required=False)

    success = graphene.Boolean()
    error = graphene.String()
    invalid_media_url = graphene.Boolean()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, media_url=None, genre=None, email_when_grouped=False, feedback_prompt=None):
        user = info.context.user
        if user.is_anonymous:
            return CreateFeedbackRequest(
                success=False,
                error='Not logged in.',
                invalid_media_url=False,
            )

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        # Validate the media url, if one exists.
        media_type = None
        if media_url:
            try:
                media_type = validate_media_url(media_url)
            except ValidationError as e:
                return CreateFeedbackRequest(
                    success=False,
                    error=e.message,
                    invalid_media_url=True,
                )
    
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
                invalid_media_url=False,
            )

        # Reject requests for the same URL (if the other submission hasn't been grouped yet)
        # This prevents users creating multiple accounts to request the same track.
        if media_url:
            existing_track_requests = FeedbackRequest.objects.filter(
                media_url=media_url,
                feedback_group=None,
            ).count()
            if existing_track_requests > 0:
                return CreateFeedbackRequest(
                    success=False,
                    error='A request for this track is already pending.',
                    invalid_media_url=False,
                )
        
        feedback_request = FeedbackRequest(
            user=feedback_groups_user,
            media_url=media_url,
            media_type=media_type,
            feedback_prompt=feedback_prompt,
            email_when_grouped=email_when_grouped,
            genre=genre,
        )
        feedback_request.save()

        return CreateFeedbackRequest(
            success=True,
            error=None,
            invalid_media_url=False,
        )


class EditFeedbackRequest(graphene.Mutation):

    class Arguments:
        feedback_request_id = graphene.Int(required=True)
        email_when_grouped = graphene.Boolean(required=False)
        media_url = graphene.String(required=False)
        feedback_prompt = graphene.String(required=False)
        genre = graphene.String(required=False)

    success = graphene.Boolean()
    error = graphene.String()
    invalid_media_url = graphene.Boolean()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, feedback_request_id, email_when_grouped=None, media_url=None, feedback_prompt=None, genre=None):
        user = info.context.user
        if user.is_anonymous:
            return EditFeedbackRequest(
                success=False,
                error='Not logged in.',
                invalid_media_url=False,
            )

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        # Validate the media url
        media_type = None
        if media_url:
            try:
                media_type = validate_media_url(media_url)
            except ValidationError as e:
                return EditFeedbackRequest(
                    success=False,
                    error=e.message,
                    invalid_media_url=True,
                )
    
        # Reject the edit if the user does not own the request (or if it doesn't exist)
        feedback_request = FeedbackRequest.objects.filter(
            user=feedback_groups_user,
            id=feedback_request_id,
        ).first()
        if not feedback_request:
            return EditFeedbackRequest(
                success=False,
                error='You are not the owner of this feedback request.',
                invalid_media_url=False,
            )

        # Reject the edit if the request has already been assigned to a group.
        if feedback_request.feedback_group:
            return EditFeedbackRequest(
                success=False,
                error='This request has already been assigned to a feedback group and cannot be edited.',
                invalid_media_url=False,
            )
        
        feedback_request.media_url = media_url
        feedback_request.media_type = media_type
        # Allow empty feedback prompt
        if feedback_prompt is not None:
            feedback_request.feedback_prompt = feedback_prompt
        if email_when_grouped is not None:
            feedback_request.email_when_grouped = email_when_grouped
        if genre is not None:
            feedback_request.genre = genre

        feedback_request.save()

        return EditFeedbackRequest(
            success=True,
            error=None,
            invalid_media_url=False,
        )


class DeleteFeedbackRequest(graphene.Mutation):

    class Arguments:
        feedback_request_id = graphene.Int(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, feedback_request_id):
        user = info.context.user
        if user.is_anonymous:
            return DeleteFeedbackRequest(
                success=False,
                error='Not logged in.',
            )

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
    
        # Reject the deletion if the user does not own the request (or if it doesn't exist)
        feedback_request = FeedbackRequest.objects.filter(
            user=feedback_groups_user,
            id=feedback_request_id,
        ).first()
        if not feedback_request:
            return DeleteFeedbackRequest(
                success=False,
                error='You are not the owner of this feedback request.',
            )

        # Reject the deletion if the request has already been assigned to a group.
        if feedback_request.feedback_group:
            return DeleteFeedbackRequest(
                success=False,
                error='This request has already been assigned to a feedback group and cannot be edited.',
            )
        
        # No problems; delete it.
        feedback_request.delete()

        return DeleteFeedbackRequest(
            success=True,
            error=None,
        )


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


class AddFeedbackResponseReply(graphene.Mutation):

    class Arguments:
        feedback_response_id = graphene.Int(required=True)
        text = graphene.String(required=True)
        allow_replies = graphene.Boolean(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, feedback_response_id, text, allow_replies):
        user = info.context.user
        if user.is_anonymous:
            return AddFeedbackResponseReply(success=False, error='Not logged in.')

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
        
        feedback_response = FeedbackResponse.objects.filter(
            id=feedback_response_id,
        ).first()

        if not feedback_response:
            return AddFeedbackResponseReply(success=False, error='Invalid feedback_response_id')

        # Only allow the FeedbackRequest user or FeedbackResponseUser to reply.
        if not feedback_response.user == feedback_groups_user and  not feedback_response.feedback_request.user == feedback_groups_user:
            return AddFeedbackResponseReply(success=False, error='You are not authorised to reply to this feedback.')

        # The client should prevent users from replying to unsubmitted feedback, obviously,
        # but we should protect against it here anyway.
        if not feedback_response.allow_replies or not feedback_response.submitted:
            return AddFeedbackResponseReply(success=False, error='You cannot reply to this feedback.')

        # If there are other replies and one of them opted to end the conversation, don't allow a new reply.
        existing_reply_has_disallowed_replies = FeedbackResponseReply.objects.filter(
            feedback_response=feedback_response,
            allow_replies=False,
        ).count() > 0
        if existing_reply_has_disallowed_replies:
            return AddFeedbackResponseReply(success=False, error='You cannot reply to this feedback.')

        reply = FeedbackResponseReply(
            feedback_response=feedback_response,
            user=feedback_groups_user,
            text=text,
            allow_replies=allow_replies,
        )
        reply.save()

        return AddFeedbackResponseReply(success=True, error=None)


class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    create_feedback_request = CreateFeedbackRequest.Field()
    delete_feedback_request = DeleteFeedbackRequest.Field()
    edit_feedback_request = EditFeedbackRequest.Field()
    submit_feedback_response = SubmitFeedbackResponse.Field()
    rate_feedback_response = RateFeedbackResponse.Field()
    add_feedback_response_reply = AddFeedbackResponseReply.Field()

    token_auth = ObtainJSONWebTokenCaseInsensitive.Field()
    refresh_token_from_cookie = RefreshTokenFromCookie.Field()
