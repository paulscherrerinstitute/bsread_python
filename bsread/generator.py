import mflow
import time
import sys
import hashlib
import math
import struct
import json
import threading


class Generator:

    def __init__(self, port=9999, start_pulse_id=0, block=True):

        from collections import OrderedDict

        self.start_pulse_id = start_pulse_id
        self.port = port
        self.block = block
        self.channels = OrderedDict()

        # Ability to add a pre and/or post function
        self.pre_function = None
        self.post_function = None

        # Internal state
        self.data_header = None
        self.data_header_json = None
        self.main_header = None
        self.stream = None
        self.pulse_id = None

        self.status_streaming = False

    def add_channel(self, name, function=None, metadata=None):

        if not metadata:
            metadata = dict()

        if not isinstance(metadata, dict):
            raise ValueError('metadata needs to be a dictionary')

        metadata['name'] = name

        # Add channel
        self.channels[name] = Channel(function, metadata)

    def open_stream(self):
        self.stream = mflow.connect('tcp://*:%d' % self.port, queue_size=10, conn_type=mflow.BIND, mode=mflow.PUSH)

        # Data header
        self.data_header = dict()
        self.data_header['htype'] = "bsr_d-1.1"
        channels = []

        for name, channel in self.channels.items():
            channels.append(channel.metadata)

        self.data_header['channels'] = channels
        self.data_header_json = json.dumps(self.data_header)

        # Main header
        self.main_header = dict()
        self.main_header['htype'] = "bsr_m-1.1"
        self.main_header['hash'] = hashlib.md5(self.data_header_json.encode('utf-8')).hexdigest()

        self.pulse_id = self.start_pulse_id

        self.status_streaming = True

    def close_stream(self):
        self.status_streaming = False
        self.stream.disconnect()

    def send(self, data=None, interval=None):
        """
            data:       Data to be send with the message send. If no data is specified data will be retrieved from the
                        functions registered with each channel
            interval:   Interval in seconds to repeatedly execute this method
        """

        if interval and self.status_streaming:
            threading.Timer(interval, lambda: self.send(interval=interval)).start()
            # Sending the same data over and over again would not make sense - therefore data is not supported when
            # interval is specified

        # TODO - pass header metadata?
        # Call pre function if registered
        if self.pre_function:
            self.pre_function()

        current_timestamp = time.time()  # current timestamp in seconds
        current_timestamp_epoch = int(current_timestamp)
        current_timestamp_ns = int(math.modf(current_timestamp)[0] * 1e9)

        self.main_header['pulse_id'] = self.pulse_id
        self.main_header['global_timestamp'] = {"epoch": current_timestamp_epoch, "ns": current_timestamp_ns}

        # TODO optimize - have dirty flag and only re-generate if necessary
        # Send headers
        # Main header
        self.stream.send(json.dumps(self.main_header).encode('utf-8'), send_more=True, block=self.block)
        # Data header
        self.stream.send(self.data_header_json.encode('utf-8'), send_more=True, block=self.block)

        counter = 0
        count = len(self.channels) - 1  # use of count to make value timestamps unique and to detect last item
        for name, channel in self.channels.items():
            if data:
                value = data[counter]
            else:
                value = channel.function(self.pulse_id)

            self.stream.send(get_bytearray(value), send_more=True, block=self.block)
            self.stream.send(struct.pack('q', current_timestamp_epoch) + struct.pack('q', count),
                             send_more=(count > 0), block=self.block)
            count -= 1
            counter += 1

        self.pulse_id += 1

        # Call post function if registered
        if self.post_function:
            self.post_function()

    def send_data(self, *args):
        self.send(data=args)

    def generate_stream(self):

        self.open_stream()
        # self.send(interval=0.1)

        while True:
            self.send()
            time.sleep(0.01)

        # self.close_stream()


def get_bytearray(value):
    if isinstance(value, float):
        return struct.pack('d', value)
    elif isinstance(value, int):
        return struct.pack('i', value)
    elif isinstance(value, str):
        return value.encode('utf-8')
    elif isinstance(value, list):
        message = bytearray()
        for v in value:
            message.extend(get_bytearray(v))
        return message
    else:
        return bytearray(value)


class Channel:
    def __init__(self, function, metadata):
        self.function = function
        self.metadata = metadata

        # metadata needs to contain: name, type (default: float64), encoding (default: little), shape (default [1])
        if 'encoding' not in self.metadata:
            self.metadata['encoding'] = sys.byteorder
