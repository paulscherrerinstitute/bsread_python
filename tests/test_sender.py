import unittest
import numpy
import logging
logging.basicConfig(level=logging.DEBUG)  # Changeing of debug level needs to be done before the import for unit testing

import bsread.sender
from bsread.sender import sender
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

    def test__get_bytearray(self):
        value = numpy.array([1, 2, 3, 4, 5, 6], dtype=numpy.uint16).reshape((2, 3))
        bytes = bsread.sender._get_bytearray(value)

        new_value = numpy.fromstring(bytes, dtype=numpy.uint16).reshape((2, 3))
        print(new_value)

    def test__get_type(self):
        value = 1
        data_type, shape = bsread.sender._get_type(value)
        self.assertEqual(data_type, "int32")
        self.assertEqual(shape, [1])

        value = 1.2
        data_type, shape = bsread.sender._get_type(value)
        self.assertEqual(data_type, "float64")
        self.assertEqual(shape, [1])

        value = "this is a test"
        data_type, shape = bsread.sender._get_type(value)
        self.assertEqual(data_type, "string")
        self.assertEqual(shape, [1])

        value = [1, 2, 3]
        data_type, shape = bsread.sender._get_type(value)
        self.assertEqual(data_type, "int32")
        self.assertEqual(shape, [3])

        value = [1.0, 2.2, 3.4, 5.3]
        data_type, shape = bsread.sender._get_type(value)
        self.assertEqual(data_type, "float64")
        self.assertEqual(shape, [4])

        value = numpy.array([1, 2, 3], dtype=numpy.uint16)
        data_type, shape = bsread.sender._get_type(value)
        self.assertEqual(data_type, "uint16")
        self.assertEqual(shape, [3])

        value = numpy.array([1, 2, 3, 4, 5, 6], dtype=numpy.uint16).reshape((2, 3))
        print(value)
        data_type, shape = bsread.sender._get_type(value)
        self.assertEqual(data_type, "uint16")
        self.assertEqual(shape, [2, 3])

        value = numpy.float32(1.0)
        print(isinstance(value, numpy.generic))
        data_type, shape = bsread.sender._get_type(value)
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

if __name__ == '__main_ _':
    unittest.main()
