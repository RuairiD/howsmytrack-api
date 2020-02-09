import datetime

import graphene
import graphql_jwt
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.utils import timezone

from graphene_django.types import DjangoObjectType

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackGroup
from howsmytrack.core.models import FeedbackRequest
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.schema.types import FeedbackRequestType
from howsmytrack.core.schema.types import FeedbackResponseType
from howsmytrack.core.schema.types import UserType
from howsmytrack.core.schema.types import FeedbackGroupType


class Query(graphene.ObjectType):
    user_details = graphene.Field(UserType)

    feedback_group = graphene.Field(
        FeedbackGroupType,
        feedback_group_id=graphene.Int(required=True),
    )
    feedback_groups = graphene.List(FeedbackGroupType)

    unassigned_request = graphene.Field(FeedbackRequestType)

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
