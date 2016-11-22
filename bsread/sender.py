import mflow
import time
import sys
import hashlib
import math
import struct
import json
import logging
from collections import OrderedDict


# Support of "with" statement
class sender:

    def __init__(self, queue_size=10, port=9999, conn_type=mflow.BIND, mode=mflow.PUSH, block=True, start_pulse_id=0):
        self.sender = Sender(queue_size=queue_size, port=port, conn_type=conn_type, mode=mode, block=block,
                             start_pulse_id=start_pulse_id)

    def __enter__(self):
        self.sender.open()
        return self.sender

    def __exit__(self, type, value, traceback):
        self.sender.close()


class Sender:

    def __init__(self, queue_size=10, port=9999, conn_type=mflow.BIND, mode=mflow.PUSH, block=True, start_pulse_id=0):

        self.block = block
        self.queue_size = queue_size
        self.port = port
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
        self.stream = mflow.connect('tcp://*:%d' % self.port, queue_size=self.queue_size, conn_type=self.conn_type,
                                    mode=self.mode)

        # Data header
        self._create_data_header()

        # Main header
        self.main_header = dict()
        self.main_header['htype'] = "bsr_m-1.1"
        self.main_header['hash'] = hashlib.md5(self.data_header_json.encode('utf-8')).hexdigest()

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

    def close(self):
        self.stream.disconnect()
        self.status_stream_open = False

    def send(self, timestamp=time.time(), pulse_id=None, data=None, check_data=True, *args, **kwargs):
        """
            data:       Data to be send with the message send. If no data is specified data will be retrieved from the
                        functions registered with each channel
            interval:   Interval in seconds to repeatedly execute this method
        """

        # If args are specified data will be overwritten
        list_data = args if args else None
        dict_data = data if data else kwargs  # data has precedence before **kwargs

        if pulse_id:
            self.pulse_id = pulse_id

        if check_data:
            if dict_data and not self.channels.keys() == dict_data.keys():
                logging.info("Update channel metadata")
                self.channels = OrderedDict()
                for key, value in dict_data.items():
                    metadata = dict()
                    metadata['name'] = key
                    metadata['type'] = _get_type(value)
                    self.channels[key] = Channel(None, metadata)

                self._create_data_header()
            elif list_data:
                if len(list_data) != self.channels:
                    raise ValueError("Length of passed data does not correspond to configured channels")

        # Call pre function if registered
        if self.pre_function:
            self.pre_function()

        current_timestamp_epoch = int(timestamp)
        current_timestamp_ns = int(math.modf(timestamp)[0] * 1e9)

        self.main_header['pulse_id'] = self.pulse_id
        self.main_header['global_timestamp'] = {"epoch": current_timestamp_epoch, "ns": current_timestamp_ns}

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
    elif isinstance(value, list):
        message = bytearray()
        for v in value:
            message.extend(_get_bytearray(v))
        return message
    else:
        return bytearray(value)


def _get_type(value):
    if isinstance(value, float):
        return "float64"
    elif isinstance(value, int):
        return "int32"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, list):
        return _get_bytearray(value[0])


class Channel:
    def __init__(self, function, metadata):
        self.function = function
        self.metadata = metadata

        # metadata needs to contain: name, type (default: float64), encoding (default: little), shape (default [1])
        if 'encoding' not in self.metadata:
            self.metadata['encoding'] = sys.byteorder