import json
import sys
import re
import zmq
import logging

logger = logging.getLogger(__name__)


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


def configure(address, configuration_string):
    """
    Configures address with the passed configuration
    Args:
        address:        Address to configure tcp://<ioc>:<port>
        configuration_string:

    Returns: Result of the operation
    """

    logger.info("Configuring: ", address)
    logger.info("Configuration: ", configuration_string)

    ctx = zmq.Context()
    sock = zmq.Socket(ctx, zmq.REQ)
    sock.connect(address)

    sock.send_string(configuration_string)
    response = sock.recv_json()

    sock.close()
    ctx.destroy()

    return response


def read_configuration():

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

    return configuration.json()


def main():

    import argparse
    parser = argparse.ArgumentParser(description='BSREAD configuration utility')
    parser.add_argument('address', type=str, help='Address to configure, has to be in format "tcp://<address>:<port>"')
    parser.add_argument('-a', '--all', action='count', help='Stream all channels of the IOC')

    arguments = parser.parse_args()

    address = arguments.address

    import re
    if not re.match('^tcp://', address):
        print 'Protocol not defined for address - Using tcp://'
        address = 'tcp://' + address
    if not re.match('.*:[0-9]+$', address):
        print 'Port not defined for address - Using 10000'
        address += ':10000'
    if not re.match('^tcp://[a-zA-Z\.-]+:[0-9]+$', address):
        print 'Invalid URI - ' + address
        exit(-1)

    # Check if to configure all channels
    if arguments.all:
        # Sending special JSON to the IOC to configure all channels to be streamed out
        configuration_string = json.dumps({"grep": 2})
    else:
        configuration_string = read_configuration()



    response = configure(address, configuration_string)

    print(response)


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

    main()

