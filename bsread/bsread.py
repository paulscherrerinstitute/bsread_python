import mflow
import zmq
import json
import time
import sys
import hashlib
import math
import struct

from .handlers.compact import Handler


PULL = zmq.PULL
PUSH = zmq.PUSH
PUB = zmq.PUB
SUB = zmq.SUB

CONNECT = "connect"
BIND = "bind"


# Support of "with" statement
class source:

    def __init__(self, host=None, port=9999, config_port=None, conn_type=CONNECT, mode=PULL,
                 channels=None, config_address=None, all_channels=False, dispatcher_url='http://dispatcher-api.psi.ch/sf'):
        self.source = Source(host=host, port=port, config_port=config_port, conn_type=conn_type, mode=mode,
                             channels=channels, config_address=config_address, all_channels=all_channels,
                             dispatcher_url=dispatcher_url)

    def __enter__(self):
        self.source.connect()
        return self.source

    def __exit__(self, type, value, traceback):
        self.source.disconnect()


class Source:

    def __init__(self, host=None, port=9999, config_port=None, conn_type=CONNECT, mode=PULL,
                 channels=None, config_address=None, all_channels=False,
                 dispatcher_url='http://dispatcher-api.psi.ch/sf'):
        """

        Args:
            host:           Source to connect to. If no source is set library will try to connect to the dispatching
                            layer.
            port:           Data port of source - only applies if host parameter is set
            config_port:    Configuration port of source - only applies if host parameter is set
            conn_type:      Specifies whether to connect or bind to the specified data socket - i.e. whether to
                            connect to the source or whether the source connects to this instance - values: CONNECT
                            or BIND
            mode:           Data delivery mode - values: PULL or PUB
            channels:       List of channels that should be in the stream. This is either a list of channel names and/or
                            a list of dictionaries specifying the desired channel configuration.
                            Example: ['ChannelA', {'name': 'ChannelC', 'modulo': 10},
                                    {'name': 'ChannelC', 'modulo': 10, 'offset': 1}]
                            If this option is present the IOC or the dispatching layer gets configured depending on
                            whether the host parameter is set. host=None > use of dispatching layer, and this parameter
                            must be specified
            config_address: Specific configuration address of the (hardware) source. This only applies if host parameter
                            is set.
            all_channels:   Whether to configure all channels to be streamed. This only appiles if host parameter is
                            set.
            dispatcher_url: URL of the dispatcher api
        """

        self.use_dispatching_layer = False

        if not config_port:
            config_port = port + 1

        self.host = host
        self.port = port
        self.config_port = config_port
        self.conn_type = conn_type
        self.mode = mode

        self.dispatcher_url = dispatcher_url

        if host:  # If a host is specified we assume a direct connection to the source
            self.address = 'tcp://'+self.host+':'+str(self.port)
            self.config_address = 'tcp://'+self.host+':'+str(self.config_port)

            if channels is not None or all_channels:
                # Reconfigure source for given channels
                if config_address:
                    self.config_address = config_address

                if all_channels:
                    request = {"grep": 2}
                else:
                    if channels:  # List is not empty
                        channel_list = []
                        for item in channels:
                            if isinstance(item, str):  # Support channel only list
                                channel_list.append({"name": item})
                            elif isinstance(item, dict):
                                # Ensure that we send an sane dictionary to the REST API
                                channel_config = dict()
                                channel_config['name'] = item['name']
                                if 'modulo' in item:
                                    channel_config['modulo'] = item['modulo']
                                if 'offset' in item:
                                    channel_config['offset'] = item['offset']

                                channel_list.append(channel_config)
                        request = {"channels": channel_list}
                    else:
                        request = {"channels": []}

                from . import config
                config.zmq_rpc(self.config_address, json.dumps(request))

        else:  # Otherwise we expect to connect to the dispatching layer

            self.use_dispatching_layer = True

            if channels is None:
                raise Exception('Channels need to be specified while connecting to the dispatching layer')

            # Request stream from dispatching layer
            from . import dispatcher
            dispatcher.base_url = self.dispatcher_url

            stream_type = 'push_pull' if self.mode == PULL else 'pub_sub'
            self.address = dispatcher.request_stream(channels, stream_type=stream_type)

            # # TODO remove Workaround
            # import re
            # self.address = re.sub('psivpn129.psi.ch', 'localhost', self.address)
            # print(self.address)

            # IMPORTANT: As the stream will be cleaned up after some time of inactivity (no connection),
            # make sure that the connect statement is issued very quick

        self.stream = None
        self.handler = Handler()

    def connect(self):
        self.stream = mflow.connect(self.address, conn_type=self.conn_type, mode=self.mode)
        return self  # Return self to be backward compatible

    def disconnect(self):
        try:
            self.stream.disconnect()
        finally:
            # # TODO remove Workaround
            # import re
            # self.address = re.sub('localhost', 'psivpn129.psi.ch', self.address)
            # print(self.address)

            from . import dispatcher
            dispatcher.base_url = self.dispatcher_url
            dispatcher.remove_stream(self.address)

    def receive(self):
        return self.stream.receive(handler=self.handler.receive)


class Generator:

    def __init__(self, port=9999, start_pulse_id=0, block=True):

        from collections import OrderedDict

        self.start_pulse_id = start_pulse_id
        self.port = port
        self.block = block
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
        data_header['htype'] = "bsr_d-1.1"
        channels = []

        for name, channel in self.channels.items():
            channels.append(channel.metadata)

        data_header['channels'] = channels
        data_header_json = json.dumps(data_header)

        # Main header
        main_header = dict()
        main_header['htype'] = "bsr_m-1.1"
        main_header['hash'] = hashlib.md5(data_header_json.encode('utf-8')).hexdigest()

        pulse_id = self.start_pulse_id

        while True:

            current_timestamp = time.time()  # current timestamp in seconds
            current_timestamp_epoch = int(current_timestamp)
            current_timestamp_ns = int(math.modf(current_timestamp)[0]*1e9)

            main_header['pulse_id'] = pulse_id
            main_header['global_timestamp'] = {"epoch": current_timestamp_epoch, "ns": current_timestamp_ns}

            # Send headers
            stream.send(json.dumps(main_header).encode('utf-8'), send_more=True, block=self.block)  # Main header
            stream.send(data_header_json.encode('utf-8'), send_more=True, block=self.block)  # Data header

            count = len(channels)-1  # use of count to make value timestamps unique and to detect last item
            for name, channel in self.channels.items():
                value = channel.function(pulse_id)

                stream.send(get_bytearray(value), send_more=True, block=self.block)
                stream.send(struct.pack('q', current_timestamp_epoch) + struct.pack('q', count), send_more=(count > 0), block=self.block)
                count -= 1

            pulse_id += 1

            # Todo this function need to be triggered by a timer to really have 10ms inbetween
            # Send out every 10ms
            time.sleep(0.01)


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
