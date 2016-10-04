import unittest
import logging

from bsread.generator import Generator

logging.basicConfig(level=logging.DEBUG)


def pre():
    logging.info('pre')


def post():
    logging.info('post')


class TestGenerator(unittest.TestCase):

    def setUp(self):
        # Enable debug logging
        pass

    def test_receive(self):
        from bsread import source
        from bsread import PULL
        from bsread import SUB

        # with source(channels=['Float64Waveform', 'Float64'],
        with source(channels=[{'name': 'Float64Waveform', 'modulo': 10}], mode=SUB,
                    dispatcher_url='http://localhost:8080') as stream:
            for i in range(10):
                message = stream.receive()
                print(message.data.data['Float64Waveform'].value)
                # print(message.data.data['Float64'].value)
        print('done')


if __name__ == '__main__':
    unittest.main()
