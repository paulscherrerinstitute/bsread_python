import zmq
import numpy


class Handler:

    def __init__(self):
        self.header_hash = None
        self.receive_functions = None
        self.endianness = None

    def receive(self, socket, header):
        return_value = {}

        data = []
        timestamp = []
        timestamp_offset = []
        pulse_ids = []
        pulse_id_array = []  # array of all pulse ids

        pulse_id = header['pulse_id']
        pulse_id_array.append(pulse_id)

        if socket.getsockopt(zmq.RCVMORE) and (not self.header_hash or not self.header_hash == header['hash']):
            # Interpret data header
            data_header = socket.recv_json()
            self.receive_functions = get_receive_functions(data_header)
            self.header_hash = header['hash']

            # Define endianness of data
            # > - big endian
            # < - little endian
            self.endianness = '<'  # default little endian
            if 'encoding' in data_header and data_header['encoding'] == 'big':
                self.endianness = '>'
            print "Using endianness: "+self.endianness

            return_value['data_header'] = data_header
        else:
            # Skip second header
            socket.recv()

        # Receiving data
        counter = 0
        while socket.getsockopt(zmq.RCVMORE):
            raw_data = socket.recv()
            if raw_data:
                data.append(self.receive_functions[counter][1].get_value(raw_data, endianness=self.endianness))

                if socket.getsockopt(zmq.RCVMORE):
                    raw_timestamp = socket.recv()
                    timestamp_array = numpy.fromstring(raw_timestamp, dtype=self.endianness+'u8')
                    # secPastEpoch = value[0]
                    # nsec = value[1]
                    timestamp.append(timestamp_array[0])
                    timestamp_offset.append(timestamp_array[1])
                    pulse_ids.append(pulse_id)
            else:
                data.append(None)
                timestamp.append(None)
                timestamp_offset.append(None)
                pulse_ids.append(None)
            counter += 1

        # pop the last None value because of the last empty submessage that terminates the message
        data.pop()
        timestamp.pop()
        timestamp_offset.pop()
        pulse_ids.pop()

        # Todo need to add some more error checking

        return_value['header'] = header
        return_value['pulse_id_array'] = pulse_id_array

        return_value['data'] = data
        return_value['timestamp'] = timestamp
        return_value['timestamp_offset'] = timestamp_offset
        return_value['pulse_ids'] = pulse_ids

        return return_value


# Supporting functions ...

def get_receive_functions(data_header):

    functions = []
    for channel in data_header['channels']:
        if 'type' in channel:
            if channel['type'].lower() == 'double':
                functions.append((channel, NumberProvider('f8')))
            if channel['type'].lower() == 'float':
                functions.append((channel, NumberProvider('f4')))
            if channel['type'].lower() == 'integer':
                functions.append((channel, NumberProvider('i4')))
            if channel['type'].lower() == 'long':
                functions.append((channel, NumberProvider('i4')))
            if channel['type'].lower() == 'ulong':
                functions.append((channel, NumberProvider('u4')))
            if channel['type'].lower() == 'short':
                functions.append((channel, NumberProvider('i2')))
            if channel['type'].lower() == 'ushort':
                functions.append((channel, NumberProvider('u2')))
            if channel['type'].lower() == 'string':
                functions.append((channel, StringProvider()))
        else:
            functions.append((channel, NumberProvider('f8')))

    return functions


# numpy type definitions can be found at: http://docs.scipy.org/doc/numpy/reference/arrays.dtypes.html
class NumberProvider:
    def __init__(self, dtype):
        self.dtype = dtype

    def get_value(self, raw_data, endianness='<'):
        value = numpy.fromstring(raw_data, dtype=endianness+self.dtype)
        if len(value) > 1:
            return value
        else:
            return value[0]


class StringProvider:
    def __init__(self):
        pass

    def get_value(self, raw_data, endianness='<'):
        # endianness does not make sens in this function
        return raw_data