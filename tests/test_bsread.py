import logging
import unittest

from bsread.data.helpers import get_value_reader


logging.basicConfig(level=logging.DEBUG)


def pre():
    logging.info("pre")


def post():
    logging.info("post")


class TestGenerator(unittest.TestCase):

    def setUp(self):
        # Enable debug logging
        pass

    # def test_receive(self):
    #     from bsread import Source
    #     from bsread import SUB
    #
    #     # with Source(channels=['Float64Waveform', 'Float64'],
    #     with Source(channels=[{'name': 'Float64Waveform', 'modulo': 10}], mode=SUB,
    #                 dispatcher_url='http://localhost:8080') as stream:
    #         for i in range(10):
    #             message = stream.receive()
    #             print(message.data.data['Float64Waveform'].value)
    #             # print(message.data.data['Float64'].value)
    #     print('done')

    def test_receive_timeout(self):
        from bsread import Sender, Source

        with Source(host="localhost", port=9999, receive_timeout=10) as in_stream:

            with Sender(queue_size=10) as stream:

                # Send Data
                # stream.send(one=1, two=2)
                # stream.send(one=3, two=4)

                # Receive and check data
                # If timeout is not working - this will hang forever - and therefore the test will fail
                message = in_stream.receive()
                if message:
                    print(message.data.data["one"].value)

                self.assertIsNone(message)

    def test_receive_filter(self):
        from bsread import Sender, Source

        def filter_method(m):
            print(m.data.data["two"].value)
            return m.data.data["two"].value <= 4

        with Source(host="localhost", port=9999) as in_stream:

            with Sender(queue_size=10) as stream:

                # Send Data
                stream.send(one=1, two=12.0)
                stream.send(one=2, two=4)
                stream.send(one=3, two=10)
                stream.send(one=4, two=9.5)

                # Receive and check data
                # If timeout is not working - this will hang forever - and therefore the test will fail
                message = in_stream.receive(filter=lambda m: m.data.data["two"].value <= 4)
                # message = in_stream.receive(filter=filter_method)
                print(message.data.data["one"].value)
                # message = in_stream.receive(filter=filter_method)

    def test_failed_conversion(self):
        channel_type = "int32"
        compression = None
        endianness = "<"
        value = 10

        value_reader = get_value_reader(channel_type, compression, shape=None, endianness=endianness)

        result = value_reader(value.to_bytes(4, byteorder="little"))
        self.assertEqual(value, result)

        result = value_reader(value.to_bytes(3, byteorder="little"))
        self.assertEqual(None, result)


if __name__ == "__main__":
    unittest.main()
