import graphene
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from howsmytrack.core.models import FeedbackGroupsUser


class UpdateEmail(graphene.Mutation):

    class Arguments:
        email = graphene.String(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, email):
        user = info.context.user
        if user.is_anonymous:
            return UpdateEmail(success=False, error='Not logged in.')

        feedback_groups_user = FeedbackGroupsUser.objects.filter(
            user=user,
        ).first()

        validator = EmailValidator()
        try:
            validator(email)
        except ValidationError:
            return UpdateEmail(success=False, error="Please provide a valid email address.")

        # Don't allow users to change their email to one used by another account.
        existing_users = User.objects.filter(username__iexact=email).count()
        if existing_users > 0:
            return UpdateEmail(success=False, error="An account for that email address already exists.")

        feedback_groups_user.update_email(email)

        return UpdateEmail(success=True, error=None)
