import unittest
import numpy
import logging

import bsread.data.helpers
import bsread.sender

from bsread.data.helpers import get_channel_specs
from bsread.sender import sender
from bsread import source

logging.basicConfig(level=logging.DEBUG)  # Changeing of debug level needs to be done before the import for unit testing


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

    def test__get_bytearray(self):
        value = numpy.array([1, 2, 3, 4, 5, 6], dtype=numpy.uint16).reshape((2, 3))
        bytes = bsread.data.helpers.get_value_bytes(value)

        new_value = numpy.frombuffer(bytes, dtype=numpy.uint16).reshape((2, 3))
        print(new_value)

    def test__get_type(self):
        # Integers are 64bit.
        value = 1
        data_type, shape = get_channel_specs(value)
        self.assertEqual(data_type, "int64")
        self.assertEqual(shape, [1])

        # Floats are doubles in python 3.
        value = 1.2
        data_type, shape = get_channel_specs(value)
        self.assertEqual(data_type, "float64")
        self.assertEqual(shape, [1])

        value = "this is a test"
        data_type, shape = get_channel_specs(value)
        self.assertEqual(data_type, "string")
        self.assertEqual(shape, [1])

        value = [1, 2, 3]
        data_type, shape = get_channel_specs(value)
        self.assertEqual(data_type, "int64")
        self.assertEqual(shape, [3])

        value = [1.0, 2.2, 3.4, 5.3]
        data_type, shape = get_channel_specs(value)
        self.assertEqual(data_type, "float64")
        self.assertEqual(shape, [4])

        value = numpy.array([1, 2, 3], dtype=numpy.uint16)
        data_type, shape = get_channel_specs(value)
        self.assertEqual(data_type, "uint16")
        self.assertEqual(shape, [3])

        value = numpy.array([1, 2, 3, 4, 5, 6], dtype=numpy.uint16).reshape((2, 3))
        print(value)
        data_type, shape = get_channel_specs(value)
        self.assertEqual(data_type, "uint16")
        self.assertEqual(shape, [2, 3])

        value = numpy.float32(1.0)
        print(isinstance(value, numpy.generic))
        data_type, shape = get_channel_specs(value)
        self.assertEqual(data_type, "float32")
        self.assertEqual(shape, [1])

    def test_stream(self):
        with source(host="localhost", port=9999) as in_stream:

            with sender(queue_size=10) as stream:
                test_array = numpy.array([1, 2, 3, 4, 5, 6], dtype=numpy.uint16).reshape((2, 3))
                # Send Data
                stream.send(one=1, two=2,
                            three=test_array)
                stream.send(pulse_id=0, one=3, two=4,
                            three=test_array, four=2.0)

                # Receive and check data
                message = in_stream.receive()
                hash_m1 = message.data.hash
                self.assertEqual(message.data.pulse_id, 0)
                self.assertEqual(message.data.data["one"].value, 1)
                self.assertEqual(message.data.data["two"].value, 2)
                message = in_stream.receive()
                hash_m2 = message.data.hash
                self.assertEqual(message.data.pulse_id, 0)
                self.assertEqual(message.data.data["one"].value, 3)
                self.assertEqual(message.data.data["two"].value, 4)

                self.assertTrue(numpy.array_equal(message.data.data["three"].value, test_array))

                # Check is data header hash is different as the second message contains more channels
                self.assertTrue(hash_m1 != hash_m2, msg="{} {}".format(hash_m1, hash_m2))

    def test_send_stream(self):
        with source(host="localhost", port=9999) as in_stream:

            with sender(queue_size=1) as stream:

                # Send none data
                stream.send(one=1, two=None, three="one")

                # Receive and check data
                message = in_stream.receive()
                self.assertEqual(message.data.pulse_id, 0)
                self.assertEqual(message.data.data["one"].value, 1)
                self.assertIsNone(message.data.data["two"].value)
                self.assertEqual(message.data.data["three"].value, "one")

                # Test sending compressed stream - compression kicks in if shape > 1
                stream.send(one=[1, 2, 3, 4, 5])

                # Receive and check data
                message = in_stream.receive()
                self.assertTrue((message.data.data["one"].value == [1, 2, 3, 4, 5]).all())

    def test_timestamp(self):

        with source(host="localhost", port=9999) as in_stream:
            with sender(queue_size=10) as stream:

                stream.send(one=1, two=2)
                # import time
                # time.sleep(2)
                stream.send(one=3, two=4)

                # Receive and check data
                message_1 = in_stream.receive()
                message_2 = in_stream.receive()

                self.assertTrue(message_1.data.global_timestamp != message_2.data.global_timestamp or
                                message_1.data.global_timestamp_offset != message_2.data.global_timestamp_offset)

    def test_compression(self):

        def register_channel(stream, name, value):
            channel_type, data_shape = get_channel_specs(value)

            # Add normal channel.
            stream.add_channel("normal_" + name,
                               lambda pulse_id: value,
                               {"type": channel_type,
                                "shape": data_shape})

            # Add compressed channel.
            stream.add_channel("compressed_" + name,
                               lambda pulse_id: value,
                               {"type": channel_type,
                                "shape": data_shape,
                                "compression": "bitshuffle_lz4"})

        with source(host="localhost") as receive_stream:
            with sender() as send_stream:
                values = {
                    "array": [1, 2, 3, 4, 5],
                    "int": -12,
                    "float": 99.0,
                    "string": "testing string",
                    "numpy_array": numpy.array([1., 2., 3., 4, 5., 6], dtype=numpy.float32).reshape(2, 3),
                    "numpy_int": numpy.int64(999999),
                    "numpy_float": numpy.float64(999999.0)
                }

                # Register all test values in channels.
                for name, value in values.items():
                    register_channel(send_stream, name, value)

                send_stream.send()
                response = receive_stream.receive()

                for name, value in values.items():

                    plain_received_value = response.data.data["normal_" + name].value
                    compressed_received_value = response.data.data["compressed_" + name].value

                    # Compare numpy arrays.
                    if isinstance(plain_received_value, numpy.ndarray):
                        numpy.testing.assert_array_equal(plain_received_value, value)
                        numpy.testing.assert_array_equal(compressed_received_value, value)

                    # Everything else.
                    else:
                        self.assertEqual(plain_received_value, value, "Plain channel values not as expected")
                        self.assertEqual(compressed_received_value, value, "Compressed channel values not as expected")

    # def test_examples(self):
    #     from bsread.sender import Sender
    #     import time
    #
    #     with source(host="localhost", port=9999) as in_stream:
    #         generator = Sender()
    #         # generator.set_pre_function(pre)
    #         generator.add_channel('ABC', lambda x: x, metadata={'type': 'int32'})
    #
    #         # generator.open()
    #         try:
    #             for i in range(10):
    #                 generator.send()
    #                 time.sleep(0.01)
    #                 in_stream.receive()
    #         finally:
    #             generator.close_stream()


if __name__ == '__main_ _':
    unittest.main()
