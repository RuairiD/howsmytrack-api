import graphene
from django.db.models import Q
from django.utils import timezone

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.core.models import FeedbackResponseReply


class MarkRepliesAsRead(graphene.Mutation):
    class Arguments:
        reply_ids = graphene.List(graphene.Int, required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([self.success == other.success, self.error == other.error,])

    def mutate(self, info, reply_ids):
        user = info.context.user
        if user.is_anonymous:
            return MarkRepliesAsRead(success=False, error="Not logged in.")

        feedback_groups_user = FeedbackGroupsUser.objects.filter(user=user,).first()

        unread_replies = (
            FeedbackResponseReply.objects.exclude(user=feedback_groups_user,)
            .filter(id__in=reply_ids, time_read__isnull=True,)
            .filter(
                Q(feedback_response__user=feedback_groups_user)
                | Q(feedback_response__feedback_request__user=feedback_groups_user),
            )
            .all()
        )

        for reply in unread_replies:
            reply.time_read = timezone.now()
            reply.save()

        return MarkRepliesAsRead(success=True, error=None)
