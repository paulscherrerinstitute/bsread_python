import mflow
import zmq
import json
import time
import sys
import hashlib
import math
import struct


PULL = zmq.PULL
PUSH = zmq.PUSH
PUB = zmq.PUB
SUB = zmq.SUB

CONNECT = "connect"
BIND = "bind"


class Source:

    def __init__(self, host='', port=9999, config_port=None):
        if not config_port:
            config_port = port + 1

        self.host = host
        self.port = port
        self.config_port = config_port

        self.address = 'tcp://'+self.host+':'+str(self.port)
        self.config_address = 'tcp://'+self.host+':'+str(self.config_port)

    def connect(self, address=None, conn_type=CONNECT, mode=PULL):

        if address:
            self.address = address

        stream = mflow.connect(self.address, conn_type=conn_type, mode=mode)
        return Stream(stream)

    def request(self, channels=[], address=None, all_channels=False):

        if address:
            self.config_address = address

        if all_channels:
            request = {"grep": 2}
        else:
            if channels:  # List is not empty
                channel_list = []
                for item in channels:
                    if isinstance(item, str):  # Support channel only list
                        channel_list.append({"name": item})
                    else:
                        channel_list.append(item)
                request = {"channels": channel_list}
            else:
                request = {"channels": []}

        from . import config
        config.zmq_rpc(self.config_address, json.dumps(request))


#  Convenience class to hide the explicit specification of the receive handler to use
class Stream:

    def __init__(self, stream):

        from .handlers.compact import Handler

        self.stream = stream
        self.handler = Handler()

    def receive(self):
        return self.stream.receive(handler=self.handler.receive)

    def disconnect(self):
        self.stream.disconnect()


class Generator:

    def __init__(self, port=9999, start_pulse_id=0):

        from collections import OrderedDict

        self.start_pulse_id = start_pulse_id
        self.port = port
        self.channels = OrderedDict()

    def add_channel(self, name, function, metadata=None):

        if not metadata:
            metadata = dict()

        if not isinstance(metadata, dict):
            raise ValueError('metadata needs to be a dictionary')

        metadata['name'] = name

        # Add channel
        self.channels[name] = Channel(function, metadata)

    def generate_stream(self):

        stream = mflow.connect('tcp://*:%d' % self.port, conn_type=mflow.BIND, mode=mflow.PUSH)

        # Data header
        data_header = dict()
        data_header['htype'] = "bsr_d-1.0"
        channels = []

        for name, channel in self.channels.items():
            channels.append(channel.metadata)

        data_header['channels'] = channels
        data_header_json = json.dumps(data_header)

        # Main header
        main_header = dict()
        main_header['htype'] = "bsr_m-1.0"
        main_header['hash'] = hashlib.md5(data_header_json.encode('utf-8')).hexdigest()

        pulse_id = self.start_pulse_id

        while True:

            current_timestamp = time.time()  # current timestamp in seconds
            current_timestamp_epoch = int(current_timestamp)
            current_timestamp_ns = int(math.modf(current_timestamp)[0]*1e9)

            main_header['pulse_id'] = pulse_id
            main_header['global_timestamp'] = {"epoch": current_timestamp_epoch, "ns": current_timestamp_ns}

            # Send headers
            stream.send(json.dumps(main_header).encode('utf-8'), send_more=True)  # Main header
            stream.send(data_header_json.encode('utf-8'), send_more=True)  # Data header

            count = len(channels)-1  # use of count to make value timestamps unique and to detect last item
            for name, channel in self.channels.items():
                value = channel.function(pulse_id)
                stream.send(struct.pack('d', value), send_more=True)
                stream.send(struct.pack('q', current_timestamp_epoch) + struct.pack('q', count), send_more=(count > 0))
                count -= 1


            # for index in range(0, 200):
            #     channel = dict()
            #     channel['encoding'] = "little"
            #     channel['name'] = "CHANNEL-%d" % index
            #     channel['type'] = "double"
            #     channels.append(channel)
            #
            # channel = dict()
            # channel['encoding'] = "little"
            # channel['name'] = "CHANNEL-STRING"
            # channel['type'] = "string"
            # channels.append(channel)
            #
            # channel = dict()
            # channel['encoding'] = "little"
            # channel['name'] = "CHANNEL-ARRAY_1"
            # channel['type'] = "double"
            # channel['shape'] = [300]
            # channels.append(channel)

            # for index in range(0, 200):
            #     self.socket.send(struct.pack('d', value+index), zmq.SNDMORE)  # Data
            #     self.socket.send(struct.pack('q', current_timestamp) + struct.pack('q', 0), zmq.SNDMORE)  # Timestamp
            #     value += 0.01
            #
            # self.socket.send("hello-%d" % value, zmq.SNDMORE)  # Data
            # self.socket.send(struct.pack('q', current_timestamp) + struct.pack('q', 0), zmq.SNDMORE)  # Timestamp
            #
            # # lists need to be handled
            # msg = bytearray()
            # for index in xrange(0,300,1):
            # 	grad=(3.1415*(index)/float(200))+pulse_id/float(100)
            # 	msg.extend(struct.pack('d',math.sin((grad))))
            #
            #
            # self.socket.send(msg, zmq.SNDMORE)  # Data
            # self.socket.send(struct.pack('q', current_timestamp) + struct.pack('q', 0), zmq.SNDMORE)  # Timestamp

            pulse_id += 1

            # Todo this function need to be triggered by a timer to really have 10ms inbetween
            # Send out every 10ms
            time.sleep(0.01)


class Channel:
    def __init__(self, function, metadata):
        self.function = function
        self.metadata = metadata

        # metadata needs to contain: name, type (default: float64), encoding (default: little), shape (default [1])
        if 'encoding' not in self.metadata:
            self.metadata['encoding'] = sys.byteorder
