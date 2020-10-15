import graphql_jwt
from django.contrib.auth.models import User


class ObtainJSONWebTokenCaseInsensitive(graphql_jwt.ObtainJSONWebToken):
    """
    Retain all functionality of graphql_jwt.ObtainJSONWebToken but check if
    a user exists with the username in another case. If one exists, pass
    through the correct username instead.

    However, since some accounts were already created before this changed with
    the same email in multiple cases, we're allowing those accounts to
    persist by logging them in using the exact email address with exact casing.

    e.g.
        - if the user has the username 'davy@gmail.com', an attempt to log in
          with 'DAVY@gmail.com' will be accepted.
        - if the user has the username 'davy@gmail.com' and another has 'Davy@gmail.com',
          an attempt to log in with 'DAVY@gmail.com' will be accepted for whichever
          account was created first, while using the exact emails will guarantee
          the exact account.
    """

    class Arguments:
        pass

    @classmethod
    def mutate(cls, *args, **kwargs):
        exact_user = User.objects.filter(username=kwargs["username"]).first()
        different_case_user = User.objects.filter(
            username__iexact=kwargs["username"]
        ).first()
        if not exact_user and different_case_user:
            kwargs["username"] = different_case_user.username
        return super(ObtainJSONWebTokenCaseInsensitive, cls).mutate(*args, **kwargs,)
