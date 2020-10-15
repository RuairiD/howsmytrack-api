import graphene

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackResponse
from howsmytrack.core.models import FeedbackResponseReply
from howsmytrack.core.schema.types import FeedbackResponseReplyType


class AddFeedbackResponseReply(graphene.Mutation):
    class Arguments:
        feedback_response_id = graphene.Int(required=True)
        text = graphene.String(required=True)
        allow_replies = graphene.Boolean(required=True)

    reply = graphene.Field(FeedbackResponseReplyType)
    error = graphene.String()

    def __eq__(self, other):
        return all([self.reply == other.reply, self.error == other.error,])

    def mutate(self, info, feedback_response_id, text, allow_replies):
        user = info.context.user
        if user.is_anonymous:
            return AddFeedbackResponseReply(reply=None, error="Not logged in.")

        feedback_groups_user = FeedbackGroupsUser.objects.filter(user=user,).first()

        feedback_response = FeedbackResponse.objects.filter(
            id=feedback_response_id,
        ).first()

        if not feedback_response:
            return AddFeedbackResponseReply(
                reply=None, error="Invalid feedback_response_id"
            )

        # Only allow the FeedbackRequest user or FeedbackResponseUser to reply.
        if (
            not feedback_response.user == feedback_groups_user
            and not feedback_response.feedback_request.user == feedback_groups_user
        ):
            return AddFeedbackResponseReply(
                reply=None, error="You are not authorised to reply to this feedback."
            )

        # The client should prevent users from replying to unsubmitted feedback, obviously,
        # but we should protect against it here anyway.
        # If there are other replies and one of them opted to end the conversation, don't allow a new reply.
        if (
            not feedback_response.allow_replies
            or not feedback_response.submitted
            or not feedback_response.allow_further_replies
        ):
            return AddFeedbackResponseReply(
                reply=None, error="You cannot reply to this feedback."
            )

        reply = FeedbackResponseReply(
            feedback_response=feedback_response,
            user=feedback_groups_user,
            text=text,
            allow_replies=allow_replies,
        )
        reply.save()

        return AddFeedbackResponseReply(
            reply=FeedbackResponseReplyType.from_model(reply, feedback_groups_user,),
            error=None,
        )
