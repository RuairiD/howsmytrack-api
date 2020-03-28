from unittest.mock import Mock
from unittest.mock import patch

import graphql_jwt
from django.test import TestCase

from howsmytrack.core.schema.mutations.refresh_token_from_cookie import RefreshTokenFromCookie
from howsmytrack.schema import schema


class RefreshTokenFromCookieTest(TestCase):
    def test_refresh_token_from_cookie(self):
        context = Mock()
        info = Mock()
        info.context = Mock()
        info.context.COOKIES = {
            'JWT': 'existingtoken'
        }
        with patch.object(
            graphql_jwt.Refresh,
            'mutate',
            return_value=RefreshTokenFromCookie(
                token='newtoken',
            ),
        ) as mock_mutate:
            schema.get_mutation_type().fields['refreshTokenFromCookie'].resolver(
                context,
                info,
            )
            mock_mutate.assert_called_once_with(context, info, token='existingtoken')

    def test_refresh_token_without_cookies(self):
        context = Mock()
        info = Mock()
        info.context = Mock()
        info.context.COOKIES = {}
        with patch.object(
            graphql_jwt.Refresh,
            'mutate',
            return_value=RefreshTokenFromCookie(
                token='newtoken',
            ),
        ):
            result = schema.get_mutation_type().fields['refreshTokenFromCookie'].resolver(
                context,
                info,
            )
            self.assertIsNone(result)
