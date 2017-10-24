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

        # Not an empty ndarray, but a None.
        if raw_data.size == 0 and shape == [1]:
            return None

        # Do not reshape scalars.
        if shape is not None and shape != [1]:
            # Numpy is slowest dimension first, but bsread is fastest dimension first.
            raw_data = raw_data.reshape(shape[::-1])

        return raw_data

    @staticmethod
    def pack_data(numpy_array):
        """
        Convert numpy array to byte array.
        :param numpy_array: Numpy array to convert.
        :return: Bytes array of provided numpy array.
        """
        return numpy_array.tobytes()


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

        # If the numpy array is empty, return it as such.
        if raw_data.size == 0:
            return None

        # Uncompressed block size, big endian, int64 (long long)
        unpacked_length = struct.unpack(">q", raw_data[0:8].tobytes())[0]

        # Empty array was transmitted.
        if unpacked_length == 0:
            return numpy.array([], dtype=dtype)

        # Type of the output array.
        dtype = numpy.dtype(dtype)
        n_bytes_per_element = dtype.itemsize

        # Either the unpacked length or the dtype is wrong.
        if unpacked_length % n_bytes_per_element != 0:
            raise ValueError("Invalid unpacked length or dtype for raw bytes.")

        # How many bytes per element we use.
        n_elements = int(unpacked_length / n_bytes_per_element)

        # TODO: This is so ugly.. discuss if strings really need a shape [1].

        # shape == [1] and n_elements > 1 is used for strings.
        if shape is None or (shape == [1] and n_elements > 1):
            shape = (n_elements,)

        # Compression block size, big endian, int32 (int)
        compression_block_size = struct.unpack(">i", raw_data[8:12].tobytes())[0]

        # If shape is not provided use the original length.
        if shape is None:
            shape = (unpacked_length,)

        # Numpy is slowest dimension first, but bsread is fastest dimension first.
        shape = shape[::-1]

        # Actual data.
        byte_array = bitshuffle.decompress_lz4(raw_data[12:], block_size=compression_block_size,
                                               shape=shape, dtype=dtype)

        return byte_array

    @staticmethod
    def pack_data(numpy_array):
        """
        Compress the provided numpy array.
        :param numpy_array: Array to compress.
        :return: Header (unpacked length, compression block size) + Compressed data
        """
        # Uncompressed block size, big endian, int64 (long long)
        unpacked_length = struct.pack(">q", numpy_array.nbytes)

        # Compression block size, big endian, int32 (int)
        compression_block_size = struct.pack(">i", BitshuffleLZ4.default_compression_block_size)

        compressed_bytes = bitshuffle.compress_lz4(numpy_array, BitshuffleLZ4.default_compression_block_size).tobytes()

        return unpacked_length + compression_block_size + compressed_bytes
