import zmq
import numpy


class Handler:

    def __init__(self):
        return

    def receive(self, socket, header):
        return_value = {}
        data = []

        # header contains: "htype", "shape", "type", "frame", "endianess", "source", "encoding", "tags"

        # Receiving data
        while socket.getsockopt(zmq.RCVMORE):
            raw_data = socket.recv()
            if raw_data:
                data.append(get_image(raw_data, header['type'], header['shape']))
            else:
                data.append(None)

        return_value['header'] = header
        return_value['data'] = data
        return return_value


def get_image(raw_data, dtype, shape):
    return numpy.fromstring(raw_data, dtype=dtype, shape=shape)