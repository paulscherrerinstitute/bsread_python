import mflow
import time
import sys
import hashlib
import math
import struct
import numpy
import json
import logging
from collections import OrderedDict

PULL = mflow.PULL
PUSH = mflow.PUSH
PUB = mflow.PUB
SUB = mflow.SUB

CONNECT = "connect"
BIND = "bind"


# Support of "with" statement
class sender:

    def __init__(self, queue_size=10, port=9999, conn_type=BIND, mode=PUSH, block=True, start_pulse_id=0):
        self.sender = Sender(queue_size=queue_size, port=port, conn_type=conn_type, mode=mode, block=block,
                             start_pulse_id=start_pulse_id)

    def __enter__(self):
        self.sender.open()
        return self.sender

    def __exit__(self, type, value, traceback):
        self.sender.close()


class Sender:

    def __init__(self, queue_size=10, port=9999, address="tcp://*", conn_type=BIND, mode=PUSH, block=True, start_pulse_id=0):

        self.block = block
        self.queue_size = queue_size
        self.port = port
        self.address = address
        self.conn_type = conn_type
        self.mode = mode

        self.stream = None

        self.start_pulse_id = start_pulse_id
        self.pulse_id = None

        self.channels = OrderedDict()

        # Ability to add a pre and/or post function
        self.pre_function = None
        self.post_function = None

        # Internal state
        self.data_header = None
        self.data_header_json = None
        self.main_header = None

        self.status_stream_open = False

    def add_channel(self, name, function=None, metadata=None):

        if not metadata:
            metadata = dict()

        if not isinstance(metadata, dict):
            raise ValueError('metadata needs to be a dictionary')

        metadata['name'] = name

        # Add channel
        self.channels[name] = Channel(function, metadata)

    def open(self):
        self.stream = mflow.connect('%s:%d' % (self.address, self.port), queue_size=self.queue_size, conn_type=self.conn_type,
                                    mode=self.mode)

        # Main header
        self.main_header = dict()
        self.main_header['htype'] = "bsr_m-1.1"

        # Data header
        self._create_data_header()

        # Set initial pulse_id
        self.pulse_id = self.start_pulse_id

        # Update internal status
        self.status_stream_open = True

    def _create_data_header(self):
        self.data_header = dict()
        self.data_header['htype'] = "bsr_d-1.1"
        channels = []
        for name, channel in self.channels.items():
            channels.append(channel.metadata)
        self.data_header['channels'] = channels
        self.data_header_json = json.dumps(self.data_header)

        self.main_header['hash'] = hashlib.md5(self.data_header_json.encode('utf-8')).hexdigest()

    def close(self):
        self.stream.disconnect()
        self.status_stream_open = False

    def send(self, *args, timestamp=None, pulse_id=None, data=None, check_data=True,  **kwargs):
        """
            data:       Data to be send with the message send. If no data is specified data will be retrieved from the
                        functions registered with each channel
            interval:   Interval in seconds to repeatedly execute this method
        """

        if timestamp is None:
            timestamp = time.time()

        # If args are specified data will be overwritten
        list_data = args if args else None
        dict_data = data if data else kwargs  # data has precedence before **kwargs

        if pulse_id is not None:
            self.pulse_id = pulse_id

        if check_data:
            if dict_data:  # and not self.channels.keys() == dict_data.keys():
                logging.info("Update channel metadata")
                self.channels = OrderedDict()
                for key, value in dict_data.items():
                    metadata = dict()
                    metadata['name'] = key
                    if value is not None:
                        metadata['type'], metadata['shape'] = _get_type(value)
                    else:
                        logging.warning('Unable to determine type of channel %s - default to type=float64 shape=[1]' % key)
                        # Default to double shape one
                        metadata['type'] = "float64"
                        metadata['shape'] = [1]

                    self.channels[key] = Channel(None, metadata)

                self._create_data_header()
            elif list_data:
                if len(list_data) != len(self.channels):
                    raise ValueError("Length of passed data (%d) does not correspond to configured channels (%d)"
                                     % (len(list_data), len(self.channels)))
                # channels is Ordered dict, assumption is that channels are in the same order
                for i, k in enumerate(self.channels):
                    metadata = dict()
                    metadata['name'] = k
                    metadata['type'], metadata['shape'] = _get_type(list_data[i])
                    self.channels[k].metadata = metadata

                self._create_data_header()

        # Call pre function if registered
        if self.pre_function:
            self.pre_function()

        current_timestamp_epoch = int(timestamp)
        current_timestamp_ns = int(math.modf(timestamp)[0] * 1e9)

        self.main_header['pulse_id'] = self.pulse_id
        self.main_header['global_timestamp'] = {"sec": current_timestamp_epoch, "ns": current_timestamp_ns}

        # Send headers
        # Main header
        self.stream.send(json.dumps(self.main_header).encode('utf-8'), send_more=True, block=self.block)
        # Data header
        self.stream.send(self.data_header_json.encode('utf-8'), send_more=True, block=self.block)

        counter = 0
        count = len(self.channels) - 1  # use of count to make value timestamps unique and to detect last item
        for name, channel in self.channels.items():
            if dict_data:
                value = dict_data[name]
            elif list_data:
                value = list_data[counter]
            else:
                value = channel.function(self.pulse_id)

            self.stream.send(_get_bytearray(value), send_more=True, block=self.block)
            self.stream.send(struct.pack('q', current_timestamp_epoch) + struct.pack('q', count),
                             send_more=(count > 0), block=self.block)
            count -= 1
            counter += 1

        self.pulse_id += 1

        # Call post function if registered
        if self.post_function:
            self.post_function()

    def generate_stream(self):
        self.open()

        while True:
            self.send()
            time.sleep(0.01)


def _get_bytearray(value):
    if isinstance(value, float):
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
            message.extend(_get_bytearray(v))
        return message
    else:
        return bytearray(value)


def _get_type(value):
    if isinstance(value, float):
        return "float64", [1]
    elif isinstance(value, int):
        return "int32", [1]
    elif isinstance(value, str):
        return "string", [1]
    elif isinstance(value, numpy.ndarray):
        return value.dtype.name, list(value.shape)
    elif isinstance(value, numpy.generic):
        return value.dtype.name, [1]
    elif isinstance(value, list):
        dtype, _ = _get_type(value[0])
        return dtype, [len(value)]


class Channel:
    def __init__(self, function, metadata):
        self.function = function
        self.metadata = metadata

        # metadata needs to contain: name, type (default: float64), encoding (default: little), shape (default [1])
        if 'encoding' not in self.metadata:
            self.metadata['encoding'] = sys.byteorder
