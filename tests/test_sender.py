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

    def test_send(self):
        generator = Generator()
        generator.set_pre_function(pre)
        generator.add_channel('ABCD')
        generator.add_channel('ABCD2')
        generator.open_stream()
        generator.send_data(1.0, 1.1)
        generator.send_data(2.0, 2.1)
        generator.close_stream()

    def test_send_interval(self):
        generator = Generator()
        generator.pre_function(lambda: print("x"))
        generator.send(interval=1.0)

    # def test_stream(self):
    #     logging.info('bla')
    #     generator = Generator()
    #     generator.set_pre_function(pre)
    #     generator.add_channel('ABCD', lambda x: x * 10.0)
    #     generator.set_post_function(post)
    #     logging.info('start')
    #     logging.info(generator)
    #     generator.generate_stream()


if __name__ == '__main__':
    unittest.main()
