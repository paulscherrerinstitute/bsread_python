import numpy


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
        message.global_timestamp = header['global_timestamp']['epoch']
        message.global_timestamp_offset = header['global_timestamp']['ns']

        # Receiver data header
        if receiver.has_more() and (self.header_hash is None or not self.header_hash == header['hash']):

            self.header_hash = header['hash']

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
                endianness = self.receive_functions[counter][0]["encoding"];
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
        if 'type' in channel:
            if channel['type'].lower() == 'double':
                functions.append((channel, NumberProvider('f8')))
            elif channel['type'].lower() == 'float':
                functions.append((channel, NumberProvider('f4')))
            elif channel['type'].lower() == 'integer':
                functions.append((channel, NumberProvider('i4')))
            elif channel['type'].lower() == 'long':
                functions.append((channel, NumberProvider('i4')))
            elif channel['type'].lower() == 'ulong':
                functions.append((channel, NumberProvider('u4')))
            elif channel['type'].lower() == 'short':
                functions.append((channel, NumberProvider('i2')))
            elif channel['type'].lower() == 'ushort':
                functions.append((channel, NumberProvider('u2')))

            elif channel['type'].lower() == 'string':
                functions.append((channel, StringProvider()))

            elif channel['type'].lower() == 'int8':
                functions.append((channel, NumberProvider('i')))
            elif channel['type'].lower() == 'uint8':
                functions.append((channel, NumberProvider('u')))
            elif channel['type'].lower() == 'int16':
                functions.append((channel, NumberProvider('i2')))
            elif channel['type'].lower() == 'uint16':
                functions.append((channel, NumberProvider('u2')))
            elif channel['type'].lower() == 'int32':
                functions.append((channel, NumberProvider('i4')))
            elif channel['type'].lower() == 'uint32':
                functions.append((channel, NumberProvider('u4')))
            elif channel['type'].lower() == 'int64':
                functions.append((channel, NumberProvider('i8')))
            elif channel['type'].lower() == 'uint64':
                functions.append((channel, NumberProvider('u8')))
            elif channel['type'].lower() == 'float32':
                functions.append((channel, NumberProvider('f4')))
            elif channel['type'].lower() == 'float64':
                functions.append((channel, NumberProvider('f8')))

            else:
                print("Unknown data type. Trying to parse as 64-bit floating-point number.")
                functions.append((channel, NumberProvider('f8')))
        else:
            print("'type' channel field not found. Trying to parse as 64-bit floating-point number.")
            functions.append((channel, NumberProvider('f8')))

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
    def __init__(self, dtype):
        self.dtype = dtype

    def get_value(self, raw_data, endianness='<'):
        try:
            value = numpy.fromstring(raw_data, dtype=endianness+self.dtype)
            if len(value) > 1:
                return value
            else:
                return value[0]
        except:
            return None


class StringProvider:
    def __init__(self):
        pass

    def get_value(self, raw_data, endianness='<'):
        # endianness does not make sens in this function
        return raw_data.decode()


class Message:
    def __init__(self):
        from collections import OrderedDict

        self.pulse_id = None
        self.global_timestamp = None
        self.global_timestamp_offset = None
        self.data = OrderedDict()  # Dictionary of values

        self.format_changed = False


class Value:
    def __init__(self):
        self.value = None
        self.timestamp = None
        self.timestamp_offset = None
