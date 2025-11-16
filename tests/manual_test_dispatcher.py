import datetime
import logging
import unittest


logging.basicConfig(level=logging.DEBUG)


class TestDispatcher(unittest.TestCase):

    def test_update_ttl(self):
        from bsread import dispatcher

        channels = ["SLG-LSCP2-FNS:CH7:VAL_GET"]
        timestamp = datetime.datetime.now()
        start = timestamp - datetime.timedelta(seconds=0.8)  # keep all data up to 0.8 seconds before the interlock
        end = timestamp + datetime.timedelta(seconds=0.1)
        ttl = datetime.timedelta(days=1)

        dispatcher.update_ttl(channels, start, end, ttl)





if __name__ == "__main__":
    unittest.main()



