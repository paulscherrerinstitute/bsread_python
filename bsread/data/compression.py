import struct

import bitshuffle
import numpy


class NoCompression:
    @staticmethod
    def unpack_data(raw_string, dtype, shape=None):
        """
        Convert raw bytes into the specified numpy type.
        :param raw_string: Raw bytes to convert.
        :param dtype: dtype to use for the result.
        :param shape: Shape of the result.
        :return: Numpy array of dtype and shape.
        """
        raw_data = numpy.frombuffer(raw_string, dtype=dtype)

        # Do not reshape scalars.
        if shape is not None and shape != [1]:
            raw_data = raw_data.reshape(shape)

        return raw_data

    @staticmethod
    def pack_data(bytes_array):
        return bytes_array


class BitshuffleLZ4:
    # numpy type definitions can be found at: http://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html
    @staticmethod
    def unpack_data(raw_bytes, dtype, shape=None):
        """
        Convert raw bytes into the specified numpy type.
        :param raw_bytes: Raw bytes to convert.
        :param dtype: dtype to use for the result.
        :param shape: Shape of the result.
        :return: Numpy array of dtype and shape.
        """
        # Interpret the bytes as a numpy array.
        raw_data = numpy.frombuffer(raw_bytes, dtype=numpy.uint8)

        # Uncompressed block size, big endian, int64 (long long)
        unpacked_length = struct.unpack(">q", raw_data[0:8].tobytes())[0]

        # Compression block size, big endian, int32 (int)
        compression_block_size = struct.unpack(">i", raw_data[8:12].tobytes())[0]

        # If shape is not provided use the original length.
        if shape is None:
            shape = (unpacked_length,)

        # Actual data.
        byte_array = bitshuffle.decompress_lz4(raw_data[12:], block_size=compression_block_size,
                                               shape=shape, dtype=numpy.dtype(dtype))

        return byte_array

    @staticmethod
    def pack_data(bytes_array):
        # TODO: Implement this to make the tests pass.
        pass


class NumberSerializer:
    """
    Serialization/Deserialization for numbers.
    """

    @staticmethod
    def deserialize(numpy_array):
        # Return single value arrays as a scalar.
        if len(numpy_array) == 1:
            return numpy_array[0]
        else:
            return numpy_array


class StringSerializer:
    """
    Serialization/Deserialization for strings.
    """

    @staticmethod
    def deserialize(numpy_array):
        # Return string variables as actual strings (UTF-8 is assumed).
        return numpy_array.tobytes().decode()
