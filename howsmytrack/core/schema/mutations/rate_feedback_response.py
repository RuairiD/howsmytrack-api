import graphene

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackResponse


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
