import json
import struct

import bitshuffle
import logging
import numpy


# numpy type definitions can be found at: http://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html
class BitshuffleNumberProvider:
    def __init__(self, dtype, shape=None):
        self.dtype = dtype
        self.shape = shape

    def get_value(self, raw_data, endianness='<'):
        try:

            raw_data = numpy.frombuffer(raw_data, dtype=numpy.uint8)
            # length = struct.unpack(">q", raw_data[:8].tobytes())[0]
            return bitshuffle.decompress_lz4(raw_data[12:], shape=self.shape, dtype=numpy.dtype(endianness+self.dtype))
        except:
            return None


class NumberProvider:
    def __init__(self, dtype, shape=None):
        self.dtype = dtype
        self.shape = shape

    def get_value(self, raw_data, endianness='<'):
        try:
            value = numpy.fromstring(raw_data, dtype=endianness+self.dtype)
            if len(value) > 1:
                if self.shape:
                    value = value.reshape(self.shape)
                return value
            else:
                return value[0]
        except:
            logging.warning('Unable to decode value - returning None')
            return None


class NoneProvider:
    def __init__(self):
        pass

    def get_value(self, raw_data, endianness='<'):
        # endianness does not make sens in this function
        return None


class StringProvider:
    def __init__(self):
        pass

    def get_value(self, raw_data, endianness='<'):
        # endianness does not make sens in this function
        try:
            return raw_data.decode()
        except:
            return None


class BitshuffleStringProvider:
    def __init__(self):
        pass

    def get_value(self, raw_data, endianness='<'):
        # endianness does not make sens in this function

        try:
            raw_data = numpy.frombuffer(raw_data, dtype=numpy.uint8)
            length = struct.unpack(">q", raw_data[:8].tobytes())[0]
            byte_array = bitshuffle.decompress_lz4(raw_data[12:], shape=(length,), dtype=numpy.dtype('uint8'))
            return byte_array.tobytes().decode()
        except:
            return None


class BitshuffleDataHeaderProvider(object):
    def __call__(self, data_header_bytes):
        data_header_bytes = numpy.frombuffer(data_header_bytes, dtype=numpy.uint8)
        length = struct.unpack(">q", data_header_bytes[:8].tobytes())[0]
        byte_array = bitshuffle.decompress_lz4(data_header_bytes[12:], shape=(length,),
                                               dtype=numpy.dtype('uint8'))

        return byte_array.tobytes().decode()


def get_data_header(header, receiver):
    """
    Based on the main header, get the data header.
    :param header: Main header.
    :param receiver: Receiver.
    :return: Data header.
    """
    # Bitshuffle lz4 compressed data header.
    if header.get('dh_compression') == 'bitshuffle_lz4':
        data_header_bytes = receiver.next()
        return json.loads(BitshuffleDataHeaderProvider(data_header_bytes))
    # Data header without compression.
    elif 'dh_compression' not in header:
        return receiver.next(as_json=True)
    # Unknown compression?
    else:
        raise ValueError("Unknown data header compression '%s'." % header.get('dh_compression'))


# Mapping from type to dtype + provider (based on compression)
number_provider_mapping = {
    'double': ('f8', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'float': ('f4', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'integer': ('i4', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'long': ('i4', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'ulong': ('i4', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'short': ('i2', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'ushort': ('u2', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'int8': ('i1', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'uint8': ('u1', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'int16': ('i2', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'uint16': ('u2', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'int32': ('i4', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'uint32': ('u4', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'int64': ('i8', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'uint64': ('u8', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'float32': ('f4', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
    'float64': ('f8', {None: NumberProvider, 'bitshuffle_lz4': BitshuffleNumberProvider}),
}


def get_receive_functions(data_header):
    functions = []
    for channel in data_header['channels']:

        # If no channel type is specified, float64 is assumed.
        channel_type = channel['type'].lower() if 'type' in channel else None
        if channel_type is None:
            print("'type' channel field not found. Parse as 64-bit floating-point number float64 (default).")
            channel_type = "float64"

        compression = channel.get('compression', None)
        shape = channel.get("shape", None)

        # String provider is a special case, because of different provider constructor parameters.
        if channel_type == "string":
            if compression == "bitshuffle_lz4":
                functions.append((channel, BitshuffleStringProvider()))
            else:
                functions.append((channel, StringProvider()))
        # Number mapping.
        elif channel_type in number_provider_mapping:
            dtype = number_provider_mapping[channel_type][0]
            number_provider = number_provider_mapping[channel_type][1][compression]

            functions.append((channel, number_provider(dtype=dtype, shape=shape)))
        # Unknown type.
        else:
            print("Unknown data type. Adding None provider.")
            functions.append((channel, NoneProvider()))

        # Define endianness of data
        # > - big endian
        # < - little endian (default)
        channel["encoding"] = '>' if channel.get("encoding") == "big" else '<'

    return functions
