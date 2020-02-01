import datetime

import graphene
from django.utils import timezone
from graphene_django.types import DjangoObjectType

from feedbackgroups.feedbackgroups.models import FeedbackGroupsUser
from feedbackgroups.feedbackgroups.models import FeedbackGroup
from feedbackgroups.feedbackgroups.models import FeedbackRequest
from feedbackgroups.feedbackgroups.models import FeedbackResponse


class UserType(DjangoObjectType):
    username = graphene.String()
    rating = graphene.Float()


class FeedbackGroupType(DjangoObjectType):
    class Meta:
        model = FeedbackGroup


class FeedbackRequestType(DjangoObjectType):
    class Meta:
        model = FeedbackRequest


class FeedbackResponseType(DjangoObjectType):
    class Meta:
        model = FeedbackResponse


class RegisterUser(graphene.Mutation):

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        password_repeat = graphene.String(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, email, password, password_repeat):
        if password == password_repeat:
            try:
                user = FeedbackGroupsUser.create(
                    email=email,
                    password=password
                )
                user.save()
                return RegisterUser(success=bool(user.id))
            except Exception as e:
                errors = ["email", e]
                return RegisterUser(success=False, errors=errors)
        errors = ["password", "Passwords don't match."]
        return RegisterUser(success=False, errors=errors)


class CreateFeedbackRequest(graphene.Mutation):

    class Arguments:
        soundcloud_url = graphene.String(required=True)
        feedback_prompt = graphene.String(required=False)

    success = graphene.Boolean()
    error = graphene.String()

    def mutate(self, info, soundcloud_url, feedback_prompt):
        user = info.context.user
        if user.is_anonymous:
            return CreateFeedbackRequest(
                success=False,
                error='Not logged in',
            )

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
    
        # Only create a new request if user hasn't created one in the past 24 hours
        date_from = timezone.now() - datetime.timedelta(days=1)
        recent_requests = FeedbackRequest.objects.filter(
            user=feedback_groups_user,
            time_created__gte=date_from
        ).count()
        if recent_requests > 0:
            return CreateFeedbackRequest(
                success=False,
                error='Already requested within 24 hours',
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
        feedback_response.submitted = True
        feedback_response.save()

        return CreateFeedbackRequest(success=True, errors=None)


class RateFeedbackResponse(graphene.Mutation):

    class Arguments:
        feedback_response_id = graphene.Int(required=True)
        rating = graphene.Int(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, feedback_response_id, rating):
        user = info.context.user
        if user.is_anonymous:
            return SaveFeedbackResponse(success=False, errors=['Not logged in'])

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()
        
        feedback_response = FeedbackResponse.objects.filter(
            feedback_request__user=feedback_groups_user,
            id=feedback_response_id,
        ).first()

        if not feedback_response:
            return SaveFeedbackResponse(success=False, errors=['Invalid feedback_response_id'])

        if feedback_response.rating:
            return SaveFeedbackResponse(success=False, errors=['Feedback has already been rated'])

        feedback_response.rating = rating
        feedback_response.save()

        return CreateFeedbackRequest(success=True, errors=None)


class Query(graphene.ObjectType):
    user_details = graphene.UserType
    feedback_requests = graphene.List(FeedbackRequestType)
    feedback_groups = graphene.List(FeedbackGroupType)

    def resolve_user_details(self, info):
        user = info.context.user
        if user.is_anonymous:
            return None

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        return None # TODO return feedback_groups_user properly

    def resolve_feedback_requests(self, info):
        return FeedbackRequest.objects.all()

    def resolve_feedback_groups(self, info):
        user = info.context.user
        if user.is_anonymous:
            return []
        
        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        feedback_requests = FeedbackRequest.objects.filter(
            user=feedback_groups_user,
        ).all()

        return [
            feedback_request.feedback_group
            for feedback_request in feedback_requests
        ]


class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    create_feedback_request = CreateFeedbackRequest.Field()
    save_feedback_response = SaveFeedbackResponse.Field()
    submit_feedback_response = SubmitFeedbackResponse.Field()
    rate_feedback_response = RateFeedbackResponse.Field()
