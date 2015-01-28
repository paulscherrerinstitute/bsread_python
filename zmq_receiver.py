#!/usr/bin/env python


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


class BsreadUtil(object):
    """"""

    def __init__(self, mode=zmq.PULL):
        """
        Initialize ZMQ
        mode: zmq.PULL (default)
        """

        self.context = zmq.Context()
        self.socket = self.context.socket(mode)
        if mode == zmq.SUB:
            self.socket.setsockopt(zmq.SUBSCRIBE, '')

    def connect(self, address="tcp://127.0.0.1:9999", conn_type="connect", timeout=1000, queue_size=4):
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
        self.socket.RCVTIMEO = timeout
        logger.info("Connection done")

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

        # if self.socket.getsockopt(zmq.RCVMORE):
        self.header = self.socket.recv_json()

        # Todo Only do this if hash changes
        # if self.socket.getsockopt(zmq.RCVMORE):
        self.data_header = self.socket.recv_json()

        # Receiving data
        while self.socket.getsockopt(zmq.RCVMORE):
            raw_data = self.socket.recv()
            if raw_data :
                data = struct.unpack('d', raw_data)
                print data

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
            self.socket.send('')
            pulse_id += 1
            time.sleep(0.1)

    def receive_double(self):
        return self.receive_double_array()[0]

    def receive_double_array(self):
        raw_data = self.socket.recv()
        return struct.unpack('d', raw_data)

    def receive_string(self):
        raw_data = self.socket.recv()
        return struct.unpack('s', raw_data)


    def generate_receive_function(self, configuration):
        """
        Generate the most efficient receive sequence for the data part of the message
        :return:    Returns the very optimised receive function for the data part
        """
        import types

        # http://stackoverflow.com/questions/10303248/true-dynamic-and-anonymous-functions-possible-in-python

        function_string = ""
        function_string += "data = dict()\n"

        # Todo ...
        #### Probably this hast to be a list of function pointers =(
        for channel in configuration['channels']:
            print channel
            function_string += "raw_data = self.socket.recv()\n"
            if channel['type'] == 'double':
                function_string += "data['"+channel['name']+"'] = struct.unpack('d', raw_data)\n"
            if channel['type'] == 'string':
                function_string += "data['"+channel['name']+"'] = struct.unpack('s', raw_data)\n"

        # This is the last empty message
        function_string += "self.socket.recv()\n"
        function_string += "return data\n"

        # Generate function
        return types.FunctionType(compile(function_string, 'read.py', 'exec'), {})
        # return function_string

if __name__ == "__main__":
    # Startup test sender
    bsread = BsreadUtil(mode=zmq.PUSH)
    bsread.connect(address="tcp://*:9999", conn_type="bind", )
    bsread.send()
