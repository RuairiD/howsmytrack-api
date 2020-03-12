import datetime
import pytz
from unittest.mock import Mock
from unittest.mock import patch

from django.test import TestCase
from graphene.test import Client

from howsmytrack.core.models import truncate_string


DEFAULT_DATETIME = datetime.datetime(1991, 11, 21, tzinfo=pytz.utc)


class TruncateStringTest(TestCase):

    def test_truncate_string_short(self):
        string = 'a' * 40
        truncated_string = truncate_string(string)
        self.assertEqual(truncated_string, string)

    def test_truncate_string_long(self):
        string = 'a' * 75
        truncated_string = truncate_string(string)
        self.assertEqual(truncated_string, 'a' * 50 + '…')
