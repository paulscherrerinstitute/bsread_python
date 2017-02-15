import mflow
import json

from .handlers.compact import Handler


PULL = mflow.PULL
PUSH = mflow.PUSH
PUB = mflow.PUB
SUB = mflow.SUB

CONNECT = "connect"
BIND = "bind"


# Support of "with" statement
class source:

    def __init__(self, host=None, port=9999, config_port=None, conn_type=CONNECT, mode=None,
                 channels=None, config_address=None, all_channels=False,
                 dispatcher_url='https://dispatcher-api.psi.ch/sf'):
        self.source = Source(host=host, port=port, config_port=config_port, conn_type=conn_type, mode=mode,
                             channels=channels, config_address=config_address, all_channels=all_channels,
                             dispatcher_url=dispatcher_url)

    def __enter__(self):
        self.source.connect()
        return self.source

    def __exit__(self, type, value, traceback):
        self.source.disconnect()


class Source:

    def __init__(self, host=None, port=9999, config_port=None, conn_type=CONNECT, mode=None,
                 channels=None, config_address=None, all_channels=False,
                 dispatcher_url='https://dispatcher-api.psi.ch/sf', send_incomplete_messages=True):
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
            send_incomplete_messages:   Send incomplete message if dispatcher was not able to retrieve all data for a
                                        given pulse-id
        """

        self.use_dispatching_layer = False

        if not config_port:
            config_port = port + 1

        self.host = host
        self.port = port
        self.config_port = config_port
        self.conn_type = conn_type

        self.dispatcher_url = dispatcher_url

        if host:  # If a host is specified we assume a direct connection to the source
            self.mode = mode if mode else PULL  # Set default mode for point to point to push/pull
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
            self.mode = mode if mode else SUB  # Set default mode for point to point to pub/sub
            self.use_dispatching_layer = True

            if channels is None:
                raise Exception('Channels need to be specified while connecting to the dispatching layer')

            # Request stream from dispatching layer
            from . import dispatcher
            dispatcher.base_url = self.dispatcher_url

            stream_type = 'push_pull' if self.mode == PULL else 'pub_sub'
            self.address = dispatcher.request_stream(channels, stream_type=stream_type,
                                                     send_incomplete_messages=send_incomplete_messages)

            # # TODO REMOVE Workaround
            # import re
            # self.address = re.sub('psivpn128.psi.ch', 'localhost', self.address)
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
            # # TODO REMOVE Workaround
            # import re
            # self.address = re.sub('localhost', 'psivpn128.psi.ch', self.address)
            # print(self.address)

            if self.use_dispatching_layer:
                from . import dispatcher
                dispatcher.base_url = self.dispatcher_url
                dispatcher.remove_stream(self.address)

    def receive(self):
        return self.stream.receive(handler=self.handler.receive)


