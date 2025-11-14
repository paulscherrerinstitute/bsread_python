import datetime
import json
import logging
import unittest
from unittest import mock

import bsread.dispatcher


logging.basicConfig(level=logging.DEBUG)  # Changing of debug level needs to be done before the import for unit testing


def pre():
    logging.info("pre")


def post():
    logging.info("post")


def mocked_requests_post(*args, **kwargs):
    print(args, kwargs)

    response = mock.MagicMock()
    response.ok = "OK"
    return response


class TestDispatcher(unittest.TestCase):

    @mock.patch("bsread.dispatcher.requests.post", side_effect=mocked_requests_post)
    def test_update_ttl(self, mock_post):

        ttl = datetime.timedelta(weeks=520)  # keep data for ~10 years
        start = datetime.datetime.now() - datetime.timedelta(seconds=1)
        end = datetime.datetime.now() + datetime.timedelta(seconds=1)

        bsread.dispatcher.update_ttl(["one",
                                      "sf-rf-databuffer/two",
                                      "sf-imagebuffer/three",
                                      "sf-archiverappliance/four",
                                      "bla/five",
                                      "sf-databuffer/six"],
                                     start, end, ttl, base_url="https://dispatcher-api.psi.ch/sf-test")

        requested_channels = json.loads(mock_post.call_args[1]["data"])["channels"]
        print(requested_channels)
        self.assertEqual(requested_channels[0]["name"], "one")
        self.assertEqual(requested_channels[0]["backend"], "sf-test")
        self.assertEqual(requested_channels[1]["name"], "two")
        self.assertEqual(requested_channels[1]["backend"], "sf-rf-databuffer")
        self.assertEqual(requested_channels[2]["name"], "three")
        self.assertEqual(requested_channels[2]["backend"], "sf-imagebuffer")
        self.assertEqual(requested_channels[3]["name"], "four")
        self.assertEqual(requested_channels[3]["backend"], "sf-archiverappliance")
        self.assertEqual(requested_channels[4]["name"], "five")
        self.assertEqual(requested_channels[4]["backend"], "bla")
        self.assertEqual(requested_channels[5]["name"], "six")
        self.assertEqual(requested_channels[5]["backend"], "sf-databuffer")

        # second series of test, having a trailing "/" in the base_url

        bsread.dispatcher.update_ttl(["one"],
                                     start, end, ttl, base_url="https://dispatcher-api.psi.ch/sf-test/")

        requested_channels = json.loads(mock_post.call_args[1]["data"])["channels"]
        print(requested_channels)
        self.assertEqual(requested_channels[0]["name"], "one")
        self.assertEqual(requested_channels[0]["backend"], "sf-test")


if __name__ == "__main__":
    unittest.main()
