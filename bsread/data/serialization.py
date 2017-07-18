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


def serialize_python_list(value, dtype):
    """
    Convert python list into ndarray.
    :param value: List to convert.
    :param dtype: Ignored. Type if retrieved from the list items.
    :return: Numpy array.
    """
    return numpy.array(value, dtype=dtype)


# Compression string to compression provider mapping.
compression_provider_mapping = {
    None: NoCompression,
    "none": NoCompression, "none": NoCompression,
    "bitshuffle_lz4": BitshuffleLZ4
}


# Channel type to numpy dtype and serializer mapping.
# channel_type: (dtype, deserializer)
channel_type_deserializer_mapping = {
    # Default value if no channel_type specified.
    None: ("f8", deserialize_number),
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
# type(value): (dtype, channel_type, serializer, shape)
channel_type_scalar_serializer_mapping = {
    # Default value if no channel_type specified.
    type(None): ("f8", "float64", serialize_python_number, [1]),
    float: ('f8', "float64", serialize_python_number, [1]),
    int: ('i8', "int64", serialize_python_number, [1]),
    str: ('u1', "string", serialize_python_string, [1]),
    numpy.int8: ('i1', 'int8', serialize_numpy, [1]),
    numpy.uint8: ('u1', 'uint8', serialize_numpy, [1]),
    numpy.int16: ('i2', 'int16', serialize_numpy, [1]),
    numpy.uint16: ('u2', 'uint16', serialize_numpy, [1]),
    numpy.int32: ('i4', 'int32', serialize_numpy, [1]),
    numpy.uint32: ('u4', 'uint32', serialize_numpy, [1]),
    numpy.int64: ('i8', 'int64', serialize_numpy, [1]),
    numpy.uint64: ('u8', 'uint64', serialize_numpy, [1]),
    numpy.float32: ('f4', 'float32', serialize_numpy, [1]),
    numpy.float64: ('f8', 'float64', serialize_numpy, [1]),
}
