import mflow
import zmq
import json

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
