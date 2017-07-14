import struct
import traceback
from logging import getLogger

import numpy

from bsread.data.compression import NoCompression, BitshuffleLZ4, deserialize_number, deserialize_string, \
    serialize_python_number, serialize_python_string, serialize_numpy

_logger = getLogger(__name__)

# Compression string to compression provider mapping.
compression_provider_mapping = {
    None: NoCompression,
    "bitshuffle_lz4": BitshuffleLZ4
}

# Channel type to numpy dtype and serializer mapping.
# channel_type: (dtype, deserializer)
channel_type_deserializer_mapping = {
    # Default value if no channel_type specified.
    None: ("f8", deserialize_number),
    'double': ('f8', deserialize_number),
    'float': ('f4', deserialize_number),
    'integer': ('i4', deserialize_number),
    'long': ('i4', deserialize_number),
    'ulong': ('i4', deserialize_number),
    'short': ('i2', deserialize_number),
    'ushort': ('u2', deserialize_number),
    'int8': ('i1', deserialize_number),
    'uint8': ('u1', deserialize_number),
    'int16': ('i2', deserialize_number),
    'uint16': ('u2', deserialize_number),
    'int32': ('i4', deserialize_number),
    'uint32': ('u4', deserialize_number),
    'int64': ('i8', deserialize_number),
    'uint64': ('u8', deserialize_number),
    'float32': ('f4', deserialize_number),
    'float64': ('f8', deserialize_number),
    'string': ('u1', deserialize_string)
}

# Value to send to channel type and serializer mapping.
# type(value)
channel_type_serializer_mapping = {
    # Default value if no channel_type specified.
    type(None): ("f8", serialize_python_number),
    float: ('f8', "double", serialize_python_number),
    int: ('i8', "long", serialize_python_number),
    str: ('u1', "string", serialize_python_string),
    numpy.int8: ('i1', 'i1', serialize_numpy),
    numpy.uint8: ('u1', 'u1', serialize_numpy),
    numpy.int16: ('i2', 'i2', serialize_numpy),
    numpy.uint16: ('u2', 'u2', serialize_numpy),
    numpy.int32: ('i4', 'i4', serialize_numpy),
    numpy.uint32: ('u4', 'u4', serialize_numpy),
    numpy.int64: ('i8', 'i8', serialize_numpy),
    numpy.uint64: ('u8', 'u8', serialize_numpy),
    numpy.float32: ('f4', 'f4', serialize_numpy),
    numpy.float64: ('f8', 'f8', serialize_numpy)
}

# Mapping between scalar type to send and channel type.
scalar_channel_type_mapping = {
    type(None): ("float64", [1]),
    float: ("float64", [1]),
    int: ("int32", [1]),
    str: ("string", [1])
}


def get_channel_type(value):
    """
    Get the bsread channel type from the value to be sent.
    :param value: Value of which to determine the channel type.
    :raise ValueError if the channel type is unsupported.
    :return: Tuple of (value type, shape)
    """
    if value is None:
        _logger.debug('Channel Value is None - Unable to determine type of channel - default to type=float64 shape=[1]')

    value_type = type(value)

    # Check if value is a python scalar.
    if value_type in scalar_channel_type_mapping:
        return scalar_channel_type_mapping[value_type]
    elif isinstance(value, numpy.ndarray):
        return value.dtype.name, list(value.shape)
    elif isinstance(value, numpy.generic):
        return value.dtype.name, [1]
    elif isinstance(value, list):
        dtype, _ = get_channel_type(value[0])
        return dtype, [len(value)]
    # We do not support this kind of values.
    else:
        raise ValueError("Unsupported channel type %s." % value_type)


def get_channel_reader(channel):
    """
    Construct a value reader for the provided channel.
    :param channel: Channel to construct the value reader for.
    :return: Value reader.
    """
    # If no channel type is specified, float64 is assumed.
    channel_type = channel['type'].lower() if 'type' in channel else None
    if channel_type is None:
        _logger.warning("'type' channel field not found. Parse as 64-bit floating-point number float64 (default).")
        channel_type = "float64"

    compression = channel['compression'] if "compression" in channel else None
    shape = channel['shape'] if "shape" in channel else None
    endianness = channel['encoding']

    value_reader = get_value_reader(channel_type, compression, shape, endianness)
    return value_reader


def get_value_reader(channel_type, compression, shape=None, endianness=""):
    """
    Get the correct value reader for the specific channel type and compression.
    :param channel_type: Channel type.
    :param compression: Compression on the channel.
    :param shape: Shape of the data.
    :param endianness: Encoding of the channel: < (small endian) or > (big endian)
    :return: Object capable of reading the data, when get_value() is called on it.
    """
    # If the type is unknown, NoneProvider should be used.
    if channel_type not in channel_type_deserializer_mapping:
        _logger.warning("Channel type '%s' not found in mapping." % channel_type)
        # If the channel is not supported, always return None.
        return lambda x: None

    # If the compression is unknown, NoneProvider should be used.
    if compression not in compression_provider_mapping:
        _logger.warning("Channel compression '%s' not supported." % compression)
        # If the channel compression is not supported, always return None.
        return lambda x: None

    decompressor = compression_provider_mapping[compression].unpack_data
    dtype, serializer = channel_type_deserializer_mapping[channel_type]
    # Expand the dtype with the correct endianess.
    dtype = endianness + dtype

    def value_reader(raw_data):
        try:
            # Decompress and deserialize the received value.
            numpy_array = decompressor(raw_data, dtype, shape)
            return serializer(numpy_array)

        except Exception as e:
            # We do not want to throw exceptions in case we cannot decode a channel.
            _logger.warning('Unable to decode value - returning None. Exception: %s', traceback.format_exc())
            return None

    return value_reader


def get_value_bytes(value, compression=None):
    """
    Based on the value, get the compressed bytes.
    :param value: Value to compress.
    :param compression: Compression to use.
    :return: Bytes ready to be sent over the channel.
    """

    if compression not in compression_provider_mapping:
        error_message = "Channel compression '%s' not supported." % compression
        _logger.error(error_message)
        raise ValueError(error_message)

    compressor = compression_provider_mapping[compression].pack_data

    bytes_array = get_value_byte_array(value)
    compressed_bytes = compressor(bytes_array)

    return compressed_bytes


def get_value_byte_array(value):
    if value is None:
        raise RuntimeError('None value cannot be serialized')
    elif isinstance(value, float):
        return struct.pack('d', value)
    elif isinstance(value, int):
        return struct.pack('i', value)
    elif isinstance(value, str):
        return value.encode('utf-8')
    elif isinstance(value, numpy.ndarray):
        return value.tobytes()
    elif value.__class__ in [x for j in numpy.sctypes.values() for x in j if "__array_interface__" in dir(x)]:
        return value.tobytes()
    elif isinstance(value, list):
        message = bytearray()
        for v in value:
            message.extend(get_value_byte_array(v))
        return message
    else:
        return bytearray(value)
