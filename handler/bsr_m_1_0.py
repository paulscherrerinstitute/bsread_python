import zmq
import numpy


class Handler:

    def __init__(self):
        self.header_hash = None
        self.receive_functions = None

    def receive(self, socket, header):
        return_value = {}

        data = []
        timestamps = []
        if socket.getsockopt(zmq.RCVMORE) and (not self.header_hash or not self.header_hash == header['hash']):
            # Interpret data header
            data_header = socket.recv_json()
            self.receive_functions = get_receive_functions(data_header)
            self.header_hash = header['hash']

            return_value['data_header'] = data_header
        else:
            # Skip second header
            socket.recv()

        # Receiving data
        counter = 0
        while socket.getsockopt(zmq.RCVMORE):
            raw_data = socket.recv()
            if raw_data:
                data.append(self.receive_functions[counter][1](raw_data))

                if socket.getsockopt(zmq.RCVMORE):
                    raw_timestamp = socket.recv()
                    timestamp = numpy.fromstring(raw_timestamp, dtype='u8')
                    # secPastEpoch = value[0]
                    # nsec = value[1]
                    timestamps.append(timestamp)
            else:
                data.append(None)
                timestamps.append(None)
            counter += 1

        # pop the last None value because of the last empty submessage that terminates the message
        data.pop()
        timestamps.pop()

        # Todo need to add some more error checking

        return_value['header'] = header
        return_value['data'] = data
        return_value['timestamps'] = timestamps
        return return_value


# Supporting functions ...

def get_receive_functions(configuration):

    functions = []
    for channel in configuration['channels']:
        if channel['type'].lower() == 'double':
            functions.append((channel, get_double))
        if channel['type'].lower() == 'integer':
            functions.append((channel, get_integer))
        if channel['type'].lower() == 'long':
            functions.append((channel, get_long))
        if channel['type'].lower() == 'string':
            functions.append((channel, get_string))

    return functions


def get_double(raw_data):
    value = numpy.fromstring(raw_data, dtype='f8')
    if len(value) > 1:
        return value
    else:
        return value[0]


def get_integer(raw_data):
    value = numpy.fromstring(raw_data, dtype='i4')
    if len(value) > 1:
        return value
    else:
        return value[0]


def get_long(raw_data):
    value = numpy.fromstring(raw_data, dtype='i8')
    if len(value) > 1:
        return value
    else:
        return value[0]


def get_string(raw_data):
    return raw_data