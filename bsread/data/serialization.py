from logging import getLogger

import numpy

from bsread.data.compression import NoCompression, BitshuffleLZ4

_logger = getLogger(__name__)


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


def serialize_numpy(numpy_number, dtype=None):
    """
    Serialize the provided numpy array.
    :param numpy_array: Array to serialize.
    :param dtype: Ignored. Here just to have a consistent interface.
    :return: Numpy array.
    """
    # Numpy array are already the format we are looking for.
    return numpy.array([numpy_number], dtype=numpy_number.dtype)


def serialize_python_number(value, dtype):
    """
    Serialize a python number by converting it into a numpy array and getting its bytes.
    :param value: Value to serialize.
    :param dtype: Numpy value representation.
    :return: Numpy array.
    """
    return numpy.array([value], dtype=dtype)


def serialize_python_string(value, dtype):
    """
    Serialize string into numpy array.
    :param value: Value to serialize.
    :param dtype: Dtype to use (UTF-8 is assumed, use u1)
    :return: Numpy array.
    """
    return numpy.frombuffer(value.encode(), dtype=dtype)


def serialize_ndarray(value, dtype=None):
    """
    numpy.ndarrays are already serialized. Just return the same value.
    :param value: Value to return.
    :param dtype: Ignored. Here just to have a consistent interface.
    :return:
    """
    return value


def serialize_python_list(value, dtype=None):
    """
    Convert python list into ndarray.
    :param value: List to convert.
    :param dtype: Ignored. Type if retrieved from the list items.
    :return: Numpy array.
    """
    base_value = value
    while isinstance(base_value, list):
        base_value = base_value[0]

    if type(base_value) not in channel_type_serializer_mapping:
        raise ValueError("Type %s not supported as channel value." % type(base_value))
    dtype = channel_type_serializer_mapping[type(base_value)][0]

    return numpy.array(value, dtype=dtype)


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
    list: (None, None, serialize_python_list),
    numpy.int8: ('i1', 'i1', serialize_numpy),
    numpy.uint8: ('u1', 'u1', serialize_numpy),
    numpy.int16: ('i2', 'i2', serialize_numpy),
    numpy.uint16: ('u2', 'u2', serialize_numpy),
    numpy.int32: ('i4', 'i4', serialize_numpy),
    numpy.uint32: ('u4', 'u4', serialize_numpy),
    numpy.int64: ('i8', 'i8', serialize_numpy),
    numpy.uint64: ('u8', 'u8', serialize_numpy),
    numpy.float32: ('f4', 'f4', serialize_numpy),
    numpy.float64: ('f8', 'f8', serialize_numpy),
    numpy.ndarray: (None, None, serialize_ndarray)
}


# Mapping between scalar type to send and channel type.
scalar_channel_type_mapping = {
    type(None): ("float64", [1]),
    float: ("float64", [1]),
    int: ("int64", [1]),
    str: ("string", [1])
}
