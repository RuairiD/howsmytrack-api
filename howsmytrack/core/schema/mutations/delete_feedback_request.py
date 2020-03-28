import graphene

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackRequest


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
