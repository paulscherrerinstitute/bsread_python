import unittest
import _thread
import logging
logging.basicConfig(level=logging.DEBUG)  # Changeing of debug level needs to be done before the import for unit testing

from bsread.sender import Sender, sender
from bsread import source


def pre():
    logging.info('pre')


def post():
    logging.info('post')


class TestGenerator(unittest.TestCase):

    def setUp(self):
        # Enable debug logging
        pass

    # def test_send(self):
    #     generator = Sender(block=False)
    #     generator.pre_function = pre
    #     generator.add_channel('ABCD')
    #     generator.add_channel('ABCD2')
    #     generator.open()
    #     generator.send_data(1.0, 1.1)
    #     generator.send_data(2.0, 2.1)
    #     generator.close()
    #
    # def test_send_interval(self):
    #     generator = Sender()
    #     generator.pre_function = lambda: print("x")
    #     # generator.send(interval=1.0)

    def test_stream(self):

        # def receive(thread_name):
        #     try:
        #         with source(host="localhost", port=9999) as stream:
        #             message = stream.receive()
        #             self.assertEqual(message.data.data["one"].value, 1)
        #             self.assertEqual(message.data.data["two"].value, 2)
        #             message = stream.receive()
        #             self.assertEqual(message.data.data["one"].value, 3)
        #             self.assertEqual(message.data.data["two"].value, 5)
        #
        # _thread.start_new_thread(receive, ("Receive",))

        with source(host="localhost", port=9999) as in_stream:

            with sender(block=False, queue_size=10) as stream:

                # Send Data
                stream.send(one=1, two=2)
                stream.send(one=3, two=4)

                # Receive and check data
                message = in_stream.receive()
                self.assertEqual(message.data.data["one"].value, 1)
                self.assertEqual(message.data.data["two"].value, 2)
                message = in_stream.receive()
                self.assertEqual(message.data.data["one"].value, 3)
                self.assertEqual(message.data.data["two"].value, 4)

if __name__ == '__main_ _':
    unittest.main()
