#!/usr/bin/python
import json
import os
import sys
import re
import zmq

def bsread_config_send(address,req):
    print("Sending to:",address)
    ctx = zmq.Context()
    sock = zmq.Socket(ctx,zmq.REQ)
    sock.connect(address)

    sock.send_string(req)
    resp = sock.recv_json()

    sock.close()
    ctx.destroy()

    return resp

def configure_ioc(ioc_name):

    # we use an input_provider class instead of a list of lines as we
    # want to be able to have interactive input as well

    configuration = Configuration()
    while True:
        line = sys.stdin.readline()
        # ignore comments
        if re.match("^[ ,\t]*#", line):
            continue
        line = line.strip()
        if not len(line):
            break
        line = re.split("[ ,\t]+", line)
        name = line[0]
        modulo = None

        try:
            if len(line) > 1:
                modulo = float(line[1])

            offset = None
            if len(line) > 2:
                offset = int(line[2])

            configuration.channels.append(Channel(name, modulo=modulo, offset=offset))
        except ValueError:
            print("modulo (float) or offset (int) specified in wrong type - ignoring channel: "+name)

    configuration_string = configuration.json()
    print("Configuration String: ")
    print(configuration_string)

    return bsread_config_send(ioc_name,configuration_string)


class Configuration:
    def __init__(self):
        self.channels = []

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class Channel:
    def __init__(self, name, modulo=None, offset=None):
        self.name = name
        if modulo is not None:
            self.modulo = modulo
        if offset is not None:
            self.offset = offset


if __name__ == '__main__':
    """
    This utility script parses standard input and creates a BSREAD configuration
    and uploads it to the specified IOC.

    It also provides utility classes to easily assemble a configuration (e.g. interactively on an
    ipython shell)

    Example:
    configuration = Configuration()
    configuration.channels = Channel("name", modulo=100, offset=0)
    configuration.json()

    Usage:
    bsread_client.py [ioc]

    The script reads from standard input and terminates on EOF or empty lines

    An input line looks like this:
    <channel> modulo(optional, type=float ) offset(optional, type=int)
    Note that only the channel name is mandatory.

    Configuration can also be piped from any other process. This is done like this:
    echo -e "one\ntwo\nthree" | python bsread_client.py
    """

    # ioc = "tcp://localhost:9995"
    if len(sys.argv) > 1:
        ioc = sys.argv[1]

    if len(sys.argv) > 2:
        response = bsread_config_send(ioc,json.dumps({"grep":2}))
        print(response)

    response = configure_ioc(ioc)
    print(response)

