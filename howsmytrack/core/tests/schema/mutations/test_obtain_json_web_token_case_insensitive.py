from unittest.mock import Mock

import graphql_jwt
from django.test import TestCase

from howsmytrack.core.models import FeedbackGroupsUser
from howsmytrack.schema import schema


class ObtainJSONWebTokenCaseInsensitiveTest(TestCase):
    def setUp(self):
        self.user = FeedbackGroupsUser.create(
            email='graham@brightonandhovealbion.com',
            password='password',
        )
        self.user.save()

    def test_same_case(self):
        info = Mock()
        result = schema.get_mutation_type().fields['tokenAuth'].resolver(
            root=Mock(),
            info=info,
            username='graham@brightonandhovealbion.com',
            password='password',
        )
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.token)
        self.assertEqual(
            graphql_jwt.utils.jwt_decode(result.token).get('username'),
            'graham@brightonandhovealbion.com',
        )

    def test_different_case(self):
        info = Mock()
        result = schema.get_mutation_type().fields['tokenAuth'].resolver(
            root=Mock(),
            info=info,
            username='GRAHAM@brightonandhovealbion.com',
            password='password',
        )
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.token)
        self.assertEqual(
            graphql_jwt.utils.jwt_decode(result.token).get('username'),
            'graham@brightonandhovealbion.com',
        )

    def test_duplicates(self):
        """Since some accounts had already been created with the same email
        in different cases when this change was made, allow logging into these
        existing accounts using the exact email they were registered with,
        including casing.
        """
        duplicate_user = FeedbackGroupsUser.create(
            email='GRAHAM@brightonandhovealbion.com',
            password='password',
        )
        duplicate_user.save()

        info = Mock()
        result = schema.get_mutation_type().fields['tokenAuth'].resolver(
            root=Mock(),
            info=info,
            username='GRAHAM@brightonandhovealbion.com',
            password='password',
        )
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.token)
        self.assertEqual(
            graphql_jwt.utils.jwt_decode(result.token).get('username'),
            'GRAHAM@brightonandhovealbion.com',
        )

    def test_different_username(self):
        info = Mock()
        with self.assertRaises(graphql_jwt.exceptions.JSONWebTokenError):
            schema.get_mutation_type().fields['tokenAuth'].resolver(
                root=Mock(),
                info=info,
                username='lewis@brightonandhovealbion.com',
                password='password',
            )
