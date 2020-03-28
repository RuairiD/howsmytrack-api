import graphene
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import transaction

from howsmytrack.core.models import FeedbackGroupsUser


INVALID_PASSWORD_MESSAGE = 'Please choose a more secure password. Your password must contain at least 8 characters, can’t be a commonly used password (e.g. "password") and can’t be entirely numeric.'


class RegisterUser(graphene.Mutation):

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        password_repeat = graphene.String(required=True)

    success = graphene.Boolean()
    error = graphene.String()

    def __eq__(self, other):
        return all([
            self.success == other.success,
            self.error == other.error,
        ])

    def mutate(self, info, email, password, password_repeat):
        validator = EmailValidator()
        try:
            validator(email)
        except ValidationError:
            return RegisterUser(success=False, error="Please provide a valid email address.")

        # Don't allow users to sign up with the same email in a different case.
        existing_users = User.objects.filter(username__iexact=email).count()
        if existing_users > 0:
            return RegisterUser(success=False, error="An account for that email address already exists.")

        if password == password_repeat:
            try:
                validate_password(password)
            except ValidationError:
                return RegisterUser(success=False, error=INVALID_PASSWORD_MESSAGE)

            with transaction.atomic():
                user = FeedbackGroupsUser.create(
                    email=email,
                    password=password
                )
                user.save()
                return RegisterUser(success=bool(user.id))
        return RegisterUser(success=False, error="Passwords don't match.")
