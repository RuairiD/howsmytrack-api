import datetime

import graphene
import graphql_jwt
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone

from graphene_django.types import DjangoObjectType

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import FeedbackResponseReply
from howsmytrack.core.schema.types import FeedbackRequestType
from howsmytrack.core.schema.types import FeedbackResponseType
from howsmytrack.core.schema.types import FeedbackResponseRepliesType
from howsmytrack.core.schema.types import UserType
from howsmytrack.core.schema.types import FeedbackGroupType
from howsmytrack.core.schema.types import MediaInfoType
from howsmytrack.core.schema.mutation import validate_media_url


class Query(graphene.ObjectType):
    media_info = graphene.Field(
        MediaInfoType,
        media_url=graphene.String(required=True),
    )

    user_details = graphene.Field(UserType)

    feedback_group = graphene.Field(
        FeedbackGroupType,
        feedback_group_id=graphene.Int(required=True),
    )
    feedback_groups = graphene.List(FeedbackGroupType)

    unassigned_request = graphene.Field(FeedbackRequestType)

    replies = graphene.Field(
        FeedbackResponseRepliesType,
        feedback_response_id=graphene.Int(required=True),
    )

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

        # Find number of responses assigned to user which are unsubmitted.
        # Displayed as an irrtating badge to encourage the user to get on with it.
        incomplete_responses = FeedbackResponse.objects.filter(
            user=feedback_groups_user,
            submitted=False,
        ).count()

        # Find number of replies *not* sent by the user but involving a response
        # for the user's request or that the user has written feedback for.
        unread_replies = FeedbackResponseReply.objects.exclude(
            user=feedback_groups_user,
        ).filter(
            time_read__isnull=True,
        ).filter(
            Q(feedback_response__user=feedback_groups_user) | Q(feedback_response__feedback_request__user=feedback_groups_user),
        ).count()

        return UserType(
            username=user.username,
            rating=rating,
            notifications=incomplete_responses + unread_replies,
            send_reminder_emails=feedback_groups_user.send_reminder_emails,
        )

    def resolve_media_info(self, info, media_url):
        media_type = None
        try:
            media_type = validate_media_url(media_url)
        except ValidationError as e:
            return MediaInfoType(
                media_url=media_url,
                media_type=media_type,
            )

        return MediaInfoType(
            media_url=media_url,
            media_type=media_type,
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

        if not feedback_group:
            return None

        return FeedbackGroupType.from_model(feedback_group, feedback_groups_user)


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
            FeedbackGroupType.from_model(feedback_request.feedback_group, feedback_groups_user)
            for feedback_request in feedback_requests
            if feedback_request.feedback_group
        ]

    def resolve_unassigned_request(self, info):
        user = info.context.user
        if user.is_anonymous:
            return None
        
        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        feedback_request =  FeedbackRequest.objects.filter(
            user=feedback_groups_user,
            feedback_group__isnull=True,
        ).first()

        if not feedback_request:
            return None

        return FeedbackRequestType.from_model(feedback_request)

    def resolve_replies(self, info, feedback_response_id):
        user = info.context.user
        if user.is_anonymous:
            return None
        
        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        feedback_response =  FeedbackResponse.objects.filter(
            id=feedback_response_id,
        ).first()

        if not feedback_response:
            return None

        # User must have either made the request for the response or written the response.
        if not feedback_response.user == feedback_groups_user and not feedback_response.feedback_request.user == feedback_groups_user:
            return None

        # If the user submitted the original request, they cannot see any replies until the
        # feedback has been rated.
        if feedback_response.feedback_request.user == feedback_groups_user and feedback_response.rating is None:
            return None

        return FeedbackResponseRepliesType.from_feedback_response(
            feedback_response,
            feedback_groups_user,
        )
