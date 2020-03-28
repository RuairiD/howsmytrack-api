import graphene
from django.utils import timezone

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackResponse


class SubmitFeedbackResponse(graphene.Mutation):

    class Arguments:
        feedback_response_id = graphene.Int(required=True)
        feedback = graphene.String(required=True)
        allow_replies = graphene.Boolean(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, feedback_response_id, feedback, allow_replies):
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
        feedback_response.allow_replies = allow_replies
        feedback_response.save()

        return SubmitFeedbackResponse(success=True, error=None)
