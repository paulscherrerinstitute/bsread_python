import traceback
from logging import getLogger

import numpy

from bsread.data.compression import NumberSerializer, StringSerializer, NoCompression, BitshuffleLZ4

_logger = getLogger(__name__)

# Channel type to numpy dtype mapping.
channel_type_serializer_mapping = {
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

# Mapping between scalar type to send and channel type.
scalar_channel_type_mapping = {
    type(None): ("float64", [1]),
    float: ("float64", [1]),
    int: ("int32", [1]),
    str: ("string", [1])
}


def _resolve_list_type(value):
    """
    Recursive function to find the element type of a list.
    :param value: Value to resolve.
    :return: Tuple of (value type, shape)
    """
    value_type, _ = get_channel_type(value[0])
    shape = [len(value)]
    return value_type, shape

# Mapping between vector type to send and channel type.
vector_channel_type_mapping = {
    list: _resolve_list_type,
    numpy.ndarray: lambda value: (value.dtype.name, list(value.shape)),
    numpy.generic: lambda value: (value.dtype.name, [1])
}


def get_channel_type(value):
    """
    Get the bsread channel type from the value to be sent.
    :param value: Value of which to determine the channel type.
    :raise ValueError if the channel type is unsupported.
    :return: Tuple of (value type, shape)
    """
    value_type = type(value)

    # Check if value is a scalar.
    if value_type in scalar_channel_type_mapping:
        return scalar_channel_type_mapping[value_type]
    # Check if value is a vector
    elif value_type in vector_channel_type_mapping:
        return vector_channel_type_mapping[value_type](value)
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
    if channel_type not in channel_type_serializer_mapping:
        _logger.warning("Channel type '%s' not found in mapping." % channel_type)
        # If the channel is not supported, always return None.
        return lambda x: None

    # If the compression is unknown, NoneProvider should be used.
    if compression not in compression_provider_mapping:
        _logger.warning("Channel compression '%s' not supported." % compression)
        # If the channel compression is not supported, always return None.
        return lambda x: None

    decompressor = compression_provider_mapping[compression].unpack_data
    dtype, serializer = channel_type_serializer_mapping[channel_type]
    # Expand the dtype with the correct endianess.
    dtype = endianness + dtype
    # Reference the serializer deserialize method only.
    serializer = serializer.deserialize

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
    return value.encode('utf-8')
