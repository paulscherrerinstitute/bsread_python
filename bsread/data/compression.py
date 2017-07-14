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
    default_compression_block_size = 0

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
        # Uncompressed block size, big endian, int64 (long long)
        unpacked_length = struct.pack(">q", len(bytes_array))

        # Compression block size, big endian, int32 (int)
        compression_block_size = struct.pack(">i", BitshuffleLZ4.default_compression_block_size)

        compressed_bytes = bitshuffle.compress_lz4(bytes_array, BitshuffleLZ4.default_compression_block_size)

        return unpacked_length + compression_block_size + compressed_bytes


def deserialize_number(numpy_array):
    # Return single value arrays as a scalar.
    if len(numpy_array) == 1:
        return numpy_array[0]
    else:
        return numpy_array


def deserialize_string(numpy_array):
    # Return string variables as actual strings (UTF-8 is assumed).
    return numpy_array.tobytes().decode()


def serialize_numpy(numpy_array, dtype):
    # Numpy arrays are easily serializable.
    return numpy_array.tobytes()


def serialize_python_number(value, dtype):
    return numpy.array(value, dtype=dtype)


def serialize_python_string(value, dtype):
    # UTF-8 is assumed.
    return numpy.frombuffer(value.encode(), dtype=dtype)
