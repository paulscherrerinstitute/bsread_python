import unittest
import logging

logging.basicConfig(level=logging.DEBUG)


def pre():
    logging.info('pre')


def post():
    logging.info('post')


class TestGenerator(unittest.TestCase):

    def setUp(self):
        # Enable debug logging
        pass

    def test_data_consistency_check(self):
        import bsread.stats

        class A:
            pass

        statistics = A()
        statistics.duplicated_pulse_ids = 0
        statistics.missed_pulse_ids = 0
        statistics.reverted_pulse_ids = 0

        message = A()
        message.data = A()

        message.data.pulse_id = 0
        bsread.stats.data_consistency_check(message.data, statistics)

        message.data.pulse_id = 1
        bsread.stats.data_consistency_check(message.data, statistics)

        self.assertTrue(statistics.duplicated_pulse_ids == 0)
        self.assertTrue(statistics.missed_pulse_ids == 0)
        self.assertTrue(statistics.reverted_pulse_ids == 0)

        message.data.pulse_id = 3
        bsread.stats.data_consistency_check(message.data, statistics)

        self.assertTrue(statistics.duplicated_pulse_ids == 0)
        self.assertTrue(statistics.missed_pulse_ids == 1)
        self.assertTrue(statistics.reverted_pulse_ids == 0)


if __name__ == '__main__':
    unittest.main()
