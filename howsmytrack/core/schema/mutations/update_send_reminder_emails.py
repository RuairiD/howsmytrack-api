import graphene

from howsmytrack.core.models import FeedbackGroupsUser


class UpdateSendReminderEmails(graphene.Mutation):
    class Arguments:
        send_reminder_emails = graphene.Boolean(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([self.success == other.success, self.error == other.error,])

    def mutate(self, info, send_reminder_emails):
        user = info.context.user
        if user.is_anonymous:
            return UpdateSendReminderEmails(success=False, error="Not logged in.")

        feedback_groups_user = FeedbackGroupsUser.objects.filter(user=user,).first()

        feedback_groups_user.send_reminder_emails = send_reminder_emails
        feedback_groups_user.save()

        return UpdateSendReminderEmails(success=True, error=None)
