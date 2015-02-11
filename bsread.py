import zmq
import json
import hashlib
import struct
import time
import logging

# Logger configuration
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(name)s - %(message)s')


class Bsread(object):

    def __init__(self, mode=zmq.PULL):
        """
        Initialize ZMQ
        mode: zmq.PULL (default)
        """

        self.context = zmq.Context()
        self.socket = self.context.socket(mode)
        if mode == zmq.SUB:
            self.socket.setsockopt(zmq.SUBSCRIBE, '')

        self.address = None
        self.data_header = None
        self.header_hash = None
        self.receive_functions = None
        self.data_header_handler = None

    def connect(self, address="tcp://127.0.0.1:9999", conn_type="connect", timeout=None, queue_size=4):
        """
        Establish ZMQ connection
        timeout: connection timeout (default: 1000)
        address: address to connect to (default: "tcp://localhost:9999")
        conn_type: the type of connection, "connect" (default) or "bind"
        queue_size: size of 0MQ receiving queue (default: 4)
        """

        logger.info("Connecting to " + address)
        self.socket.set_hwm(queue_size)
        try:
            if conn_type == "connect":
                self.socket.connect(address)
            else:
                self.socket.bind(address)
        except:
            logger.error("Unable to connect to server. Hint: check IP address")

        if timeout:
            self.socket.RCVTIMEO = timeout

        logger.info("Connection done")
        self.address = address

    def disconnect(self):
        """Disconnects and close connection"""
        if self.socket.closed:
            logger.warn("trying to close an already closed socket... ignoring this command")
            return
        try:
            self.socket.disconnect(self.address)
            self.socket.close()
            logger.info("Disconnected")
        except:
            logger.info("Unable to disconnect properly")

    def receive(self):
        data = []
        header = self.socket.recv_json()

        if (not self.header_hash) and (not self.header_hash == header['hash']):
            # Interpret data header
            self.data_header = self.socket.recv_json()
            self.receive_functions = get_receive_functions(self.data_header)
            self.header_hash = header['hash']

            # If there is a data header handler registered, call that function
            if self.data_header_handler:
                self.data_header_handler(self.data_header)
        else:
            # Skip second header
            self.socket.recv()

        # Receiving data
        counter = 0
        while self.socket.getsockopt(zmq.RCVMORE):
            raw_data = self.socket.recv()
            if raw_data:
                data.append(self.receive_functions[counter][1](raw_data))
                #print data
            counter += 1

        # Todo need to add some more error checking
        return {"data": data, "header": header}

    def send(self):
        """
        Send test data
        """
        main_header = dict()
        main_header['htype'] = "bsr_m-1.0"

        data_header = dict()
        data_header['htype'] = "bsr_d-1.0"
        channels = []
        for index in range(0, 4):
            channel = dict()
            channel['name'] = "CHANNEL-%d" % index
            channel['type'] = "double"
            channels.append(channel)

        channel = dict()
        channel['name'] = "CHANNEL-STRING"
        channel['type'] = "string"
        channels.append(channel)

        data_header['channels'] = channels

        data_header_json = json.dumps(data_header)

        main_header['hash'] = hashlib.md5(data_header_json).hexdigest()

        pulse_id = 0
        value = 0.0

        while True:
            main_header['pulse_id'] = pulse_id
            self.socket.send_json(main_header, zmq.SNDMORE)  # Main header
            self.socket.send_string(data_header_json, zmq.SNDMORE)  # Data header
            for index in range(0, 4):
                self.socket.send(struct.pack('d', value), zmq.SNDMORE)  # Data
                value += 0.1

            self.socket.send("hello-%d" % value, zmq.SNDMORE)  # Data

            self.socket.send('')
            pulse_id += 1
            # Send out every 10ms
            time.sleep(0.01)

    def set_data_header_handler(self, handler):
        self.data_header_handler = handler


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
    value = struct.unpack('d', raw_data)
    if len(value) > 1:
        return value
    else:
        return value[0]


def get_integer(raw_data):
    value = struct.unpack('i', raw_data)
    if len(value) > 1:
        return value
    else:
        return value[0]


def get_long(raw_data):
    value = struct.unpack('l', raw_data)
    if len(value) > 1:
        return value
    else:
        return value[0]


def get_string(raw_data):
    return raw_data