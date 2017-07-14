import traceback

import numpy

from bsread.data.serialization import _logger, channel_type_deserializer_mapping, \
    compression_provider_mapping, channel_type_scalar_serializer_mapping


def get_channel_specs(value, extended=False):
    """
    Get the bsread channel specification from the value to be sent.
    :param value: Value of which to determine the channel type.
    :raise ValueError if the channel type is unsupported.
    :param extended: If False (default) return (channel_type, shape);
                     If True return (dtype, channel_type, serializer, shape)
    :return: Tuple of (channel_type, shape) or (dtype, channel_type, serializer, shape)
    """
    if value is None:
        _logger.debug('Channel Value is None - Unable to determine type of channel - default to type=float64 shape=[1]')

    # Determine ndarray channel specs.
    if isinstance(value, numpy.ndarray):
        # dtype and shape already in ndarray.
        dtype = value.dtype.type
        shape = list(value.shape)

        # Object already serialized.
        serializer = None

        # We need to retrieve only channel type.
        channel_type = channel_type_scalar_serializer_mapping[dtype][1]

    # Determine list channel specs
    elif isinstance(value, list):
        # Get to the bottom of the list.
        base_value = value
        while isinstance(base_value, list):
            base_value = base_value[0]

        # Lists have a special serializer.
        def serializer(x, y): return numpy.array(x, dtype=dtype)

        # Shape is the length of the list
        shape = [len(value)]

        # Get the basic list element type.
        dtype, channel_type, _, _ = channel_type_scalar_serializer_mapping[type(base_value)]

    # Determine scalars channel specs
    else:
        dtype, channel_type, serializer, shape = channel_type_scalar_serializer_mapping[type(value)]

    # Shape can also be a function to evaluate the shape.
    if callable(shape):
        shape = shape(value)

    # We can return an extended...
    if extended:
        return dtype, channel_type, serializer, shape
    # ...or a simple spec.
    else:
        return channel_type, shape


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

    dtype, _, serializer, _ = get_channel_specs(value, extended=True)
    compressor = compression_provider_mapping[compression].pack_data

    if serializer:
        value = serializer(value, dtype)

    compressed_bytes_array = compressor(value)

    return compressed_bytes_array
