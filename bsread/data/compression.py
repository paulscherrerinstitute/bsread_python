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
        """
        Packing data with byte arrays just return the same byte array - need this method to have the same interface.
        :param bytes_array: Byte array to return.
        :return: Same byte array that was passed to the function.
        """
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
    def pack_data(numpy_array):
        """
        Compress the provided numpy array.
        :param numpy_array: Array to compress.
        :return: Header (unpacked length, compression block size) + Compressed data
        """
        # Uncompressed block size, big endian, int64 (long long)
        unpacked_length = struct.pack(">q", len(numpy_array))

        # Compression block size, big endian, int32 (int)
        compression_block_size = struct.pack(">i", BitshuffleLZ4.default_compression_block_size)

        compressed_bytes = bitshuffle.compress_lz4(numpy_array, BitshuffleLZ4.default_compression_block_size)

        return unpacked_length + compression_block_size + compressed_bytes


def deserialize_number(numpy_array):
    """
    Return single value arrays as a scalar.
    :param numpy_array: Numpy array containing a number to deserialize.
    :return: Array or scalar, based on array size.
    """
    if len(numpy_array) == 1:
        return numpy_array[0]
    else:
        return numpy_array


def deserialize_string(numpy_array):
    """
    Return string that is serialized as a numpy array.
    :param numpy_array: Array to deserialize (UTF-8 is assumed)
    :return: String.
    """
    return numpy_array.tobytes().decode()


def serialize_numpy(numpy_array, dtype=None):
    """
    Serialize the provided numpy array.
    :param numpy_array: Array to serialize.
    :param dtype: Ignored. Here just to have a consistent interface.
    :return: Bytes array with data.
    """
    # Numpy arrays are easily serializable.
    return numpy_array.tobytes()


def serialize_python_number(value, dtype):
    """
    Serialize a python number by converting it into a numpy array and getting its bytes.
    :param value: Value to serialize.
    :param dtype: Numpy value representation.
    :return: Bytes array with data.
    """
    return numpy.array(value, dtype=dtype).tobytes()


def serialize_python_string(value, dtype):
    """
    Serialize string into numpy array.
    :param value: Value to serialize.
    :param dtype: Dtype to use (UTF-8 is assumed, use u1)
    :return: Bytes array.
    """
    return numpy.frombuffer(value.encode(), dtype=dtype).tobytes()
