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
        raw_data = numpy.fromstring(raw_string, dtype=dtype)

        # Do not reshape scalars.
        if shape is not None and shape != [1]:
            raw_data = raw_data.reshape(shape)

        return raw_data

    @staticmethod
    def pack_data():
        pass


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
    def pack_data():
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
    def serialize(value):
        pass

    @staticmethod
    def deserialize(numpy_array):
        # Return string variables as actual strings (UTF-8 is assumed).
        return numpy_array.tobytes().decode()


# Channel type to numpy dtype mapping.
channel_type_mapping = {
    # Default value if no channel_type specified.
    None: ("f8", NumberSerializer),
    'double': ('f8', NumberSerializer),
    'float': ('f4', NumberSerializer),
    'integer': ('i4', NumberSerializer),
    'long': ('i4', NumberSerializer),
    'ulong': ('i4', NumberSerializer),
    'short': ('i2', NumberSerializer),
    'ushort': ('u2', NumberSerializer),
    'int8': ('i1', NumberSerializer),
    'uint8': ('u1', NumberSerializer),
    'int16': ('i2', NumberSerializer),
    'uint16': ('u2', NumberSerializer),
    'int32': ('i4', NumberSerializer),
    'uint32': ('u4', NumberSerializer),
    'int64': ('i8', NumberSerializer),
    'uint64': ('u8', NumberSerializer),
    'float32': ('f4', NumberSerializer),
    'float64': ('f8', NumberSerializer),
    'string': ('u1', StringSerializer)
}

# Compression string to compression provider mapping.
compression_provider_mapping = {
    None: NoCompression,
    "bitshuffle_lz4": BitshuffleLZ4
}
