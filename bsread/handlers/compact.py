import numpy
import bitshuffle
import json
import struct


class Handler:

    def __init__(self):
        self.header_hash = None
        self.receive_functions = None
        self.data_header = None

    def receive(self, receiver):

        # Receive main header
        header = receiver.next(as_json=True)

        message = Message()
        message.pulse_id = header['pulse_id']
        message.hash = header['hash']
            
        if 'sec' in header['global_timestamp']:
            message.global_timestamp = header['global_timestamp']['sec']
        elif 'epoch' in header['global_timestamp']:
            message.global_timestamp = header['global_timestamp']['epoch']
        else:
            raise RuntimeError("Invalid timestamp format in BSDATA header message {}".format(message))

        message.global_timestamp_offset = header['global_timestamp']['ns']

        # Receiver data header
        if receiver.has_more() and (self.header_hash is None or not self.header_hash == header['hash']):

            self.header_hash = header['hash']

            if 'dh_compression' in header and header['dh_compression'] == 'bitshuffle_lz4':
                data_header_bytes = receiver.next()
                data_header_bytes = numpy.frombuffer(data_header_bytes, dtype=numpy.uint8)
                length = struct.unpack(">q", data_header_bytes[:8].tobytes())[0]
                byte_array = bitshuffle.decompress_lz4(data_header_bytes[12:], shape=(length,),
                                                       dtype=numpy.dtype('uint8'))
                self.data_header = json.loads(byte_array.tobytes().decode())

            else:
                # Interpret data header
                self.data_header = receiver.next(as_json=True)

            # If a message with ho channel information is received,
            # ignore it and return from function with no data.
            if not self.data_header['channels']:
                while receiver.has_more():
                    # Drain rest of the messages - if entering this code there is actually something wrong
                    raw_data = receiver.next()

                return message

            self.receive_functions = get_receive_functions(self.data_header)

            message.format_changed = True
        else:
            # Skip second header
            receiver.next()

        # Receiving data
        counter = 0

        # Todo add some more error checking
        while receiver.has_more():
            raw_data = receiver.next()
            channel_value = Value()

            if raw_data:
                endianness = self.receive_functions[counter][0]["encoding"]
                channel_value.value = self.receive_functions[counter][1].get_value(raw_data, endianness=endianness)

            if receiver.has_more():
                raw_timestamp = receiver.next()
                if raw_timestamp:
                    timestamp_array = numpy.fromstring(raw_timestamp, dtype=endianness+'u8')
                    channel_value.timestamp = timestamp_array[0]  # Second past epoch
                    channel_value.timestamp_offset = timestamp_array[1]  # Nanoseconds offset

            # TODO needs to be optimized
            channel_name = self.data_header['channels'][counter]['name']
            message.data[channel_name] = channel_value
            counter += 1

        return message


# Supporting functions ...

def get_receive_functions(data_header):

    functions = []
    for channel in data_header['channels']:
        shape = None
        if 'shape' in channel:
            shape = channel['shape']

        if 'type' in channel:
            if channel['type'].lower() == 'double':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('f8', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('f8', shape=shape)))
            elif channel['type'].lower() == 'float':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('f4', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('f4', shape=shape)))
            elif channel['type'].lower() == 'integer':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('i4', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('i4', shape=shape)))
            elif channel['type'].lower() == 'long':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('i4', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('i4', shape=shape)))
            elif channel['type'].lower() == 'ulong':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('u4', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('u4', shape=shape)))
            elif channel['type'].lower() == 'short':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('i2', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('i2', shape=shape)))
            elif channel['type'].lower() == 'ushort':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('u2', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('u2', shape=shape)))

            elif channel['type'].lower() == 'string':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleStringProvider()))
                else:
                    functions.append((channel, StringProvider()))

            elif channel['type'].lower() == 'int8':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('i1', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('i1', shape=shape)))
            elif channel['type'].lower() == 'uint8':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('u1', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('u1', shape=shape)))
            elif channel['type'].lower() == 'int16':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('i2', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('i2', shape=shape)))
            elif channel['type'].lower() == 'uint16':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('u2', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('u2', shape=shape)))
            elif channel['type'].lower() == 'int32':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('i4', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('i4', shape=shape)))
            elif channel['type'].lower() == 'uint32':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('u4', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('u4', shape=shape)))
            elif channel['type'].lower() == 'int64':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('i8', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('i8', shape=shape)))
            elif channel['type'].lower() == 'uint64':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('u8', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('u8', shape=shape)))
            elif channel['type'].lower() == 'float32':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('f4', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('f4', shape=shape)))
            elif channel['type'].lower() == 'float64':
                if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                    functions.append((channel, BitshuffleNumberProvider('f8', shape=shape)))
                else:
                    functions.append((channel, NumberProvider('f8', shape=shape)))

            else:
                print("Unknown data type. Adding None provider.")
                functions.append((channel, NoneProvider()))

        else:
            print("'type' channel field not found. Parse as 64-bit floating-point number (default).")
            if 'compression' in channel and channel['compression'] == 'bitshuffle_lz4':
                functions.append((channel, BitshuffleNumberProvider('f8', shape=shape)))
            else:
                functions.append((channel, NumberProvider('f8', shape=shape)))


        # Define endianness of data
        # > - big endian
        # < - little endian
        if 'encoding' in channel and channel['encoding'] == 'big':
            channel["encoding"] = '>'
        else:
            channel["encoding"] = '<'  # default little endian

    return functions


# numpy type definitions can be found at: http://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html
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
            return None


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


class Message:
    def __init__(self):
        from collections import OrderedDict

        self.pulse_id = None
        self.global_timestamp = None
        self.global_timestamp_offset = None
        self.hash = None
        self.data = OrderedDict()  # Dictionary of values

        self.format_changed = False


class Value:
    def __init__(self):
        self.value = None
        self.timestamp = None
        self.timestamp_offset = None
