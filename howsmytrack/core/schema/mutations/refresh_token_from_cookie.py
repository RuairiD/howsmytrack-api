import graphql_jwt


class RefreshTokenFromCookie(graphql_jwt.Refresh):
    """
    The built-in graphql_jwt.Refresh mutation requires the token to be passed as
    a parameter. This custom mutation reads the token from HttpOnly cookies
    instead to prevent frontends having to store the cookie somewhere else for access.
    """
    class Arguments:
        pass

    @classmethod
    def mutate(cls, *args, **kwargs):
        cookies = args[1].context.COOKIES
        if cookies and 'JWT' in cookies:
            kwargs['token'] = cookies['JWT']
            return super(RefreshTokenFromCookie, cls).mutate(
                *args,
                **kwargs,
            )
        # If no token cookie exists, nothing to do.
        return None
