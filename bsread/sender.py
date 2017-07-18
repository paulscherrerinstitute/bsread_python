from threading import Lock

import mflow
import time
import sys
import hashlib
import math
import struct
import json
import logging
from collections import OrderedDict

from bsread.data.serialization import compression_provider_mapping
from bsread.data.helpers import get_channel_specs, get_value_bytes

PULL = mflow.PULL
PUSH = mflow.PUSH
PUB = mflow.PUB
SUB = mflow.SUB

CONNECT = "connect"
BIND = "bind"


# Support of "with" statement
class sender:

    def __init__(self, queue_size=10, port=9999, conn_type=BIND, mode=PUSH, block=True, start_pulse_id=0,
                 data_header_compression=None):
        self.sender = Sender(queue_size=queue_size, port=port, conn_type=conn_type, mode=mode, block=block,
                             start_pulse_id=start_pulse_id, data_header_compression=data_header_compression)

    def __enter__(self):
        self.sender.open()
        return self.sender

    def __exit__(self, type, value, traceback):
        self.sender.close()


class Sender:

    def __init__(self, queue_size=10, port=9999, address="tcp://*", conn_type=BIND, mode=PUSH, block=True,
                 start_pulse_id=0, data_header_compression=None):

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
        self.data_header_bytes = None
        self.main_header = None

        self.channels_lock = Lock()

        # Raise exception if invalid compression is used.
        if data_header_compression not in compression_provider_mapping:
            raise ValueError("Data header compression '%s' not supported. Available: %s" %
                             compression_provider_mapping.keys())

        self.data_header_compression = data_header_compression
        self.status_stream_open = False

    def add_channel(self, name, function=None, metadata=None):

        if not metadata:
            metadata = dict()

        if not isinstance(metadata, dict):
            raise ValueError('metadata needs to be a dictionary')

        metadata['name'] = name

        # Add channel
        with self.channels_lock:
            self.channels[name] = Channel(function, metadata)

            # If the stream is already open, recreate the header.
            if self.status_stream_open:
                self._create_data_header()

    def open(self, no_client_action=None, no_client_timeout=None):
        self.stream = mflow.connect('%s:%d' % (self.address, self.port), queue_size=self.queue_size, conn_type=self.conn_type,
                                    mode=self.mode, no_client_action=no_client_action,
                                    no_client_timeout=no_client_timeout)

        # Main header
        self.main_header = dict()
        self.main_header['htype'] = "bsr_m-1.1"
        if self.data_header_compression:
            self.main_header['dh_compression'] = self.data_header_compression

        # Data header
        with self.channels_lock:
            self._create_data_header()

        # Set initial pulse_id
        self.pulse_id = self.start_pulse_id

        # Update internal status
        self.status_stream_open = True

    def _create_data_header(self):
        self.data_header = dict()
        self.data_header['htype'] = "bsr_d-1.1"
        self.data_header['channels'] = [channel.metadata for channel in self.channels.values()]

        self.data_header_bytes = get_value_bytes(json.dumps(self.data_header), self.data_header_compression)
        self.main_header['hash'] = hashlib.md5(self.data_header_bytes).hexdigest()

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

        # Lock the channel while sending data - prevent data corruption.
        with self.channels_lock:

            if check_data:
                if dict_data:  # and not self.channels.keys() == dict_data.keys():
                    logging.debug("Update channel metadata")
                    self.channels = OrderedDict()
                    for key, value in dict_data.items():
                        metadata = dict()
                        metadata['name'] = key
                        metadata['type'], metadata['shape'] = get_channel_specs(value)
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
                        metadata['type'], metadata['shape'] = get_channel_specs(list_data[i])
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
            self.stream.send(self.data_header_bytes, send_more=True, block=self.block)

            counter = 0
            count = len(self.channels) - 1  # use of count to make value timestamps unique and to detect last item
            for name, channel in self.channels.items():
                if dict_data:
                    value = dict_data[name]
                elif list_data:
                    value = list_data[counter]
                else:
                    value = channel.function(self.pulse_id)

                if value is None:
                    self.stream.send(b'', send_more=True, block=self.block)
                    self.stream.send(b'', send_more=(count > 0), block=self.block)
                else:
                    self.stream.send(get_value_bytes(value, channel.metadata.get("compression")), send_more=True,
                                     block=self.block)

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


class Channel:
    def __init__(self, function, metadata):
        self.function = function
        self.metadata = metadata

        # metadata needs to contain: name, type (default: float64), encoding (default: little), shape (default [1])
        if 'encoding' not in self.metadata:
            self.metadata['encoding'] = sys.byteorder
