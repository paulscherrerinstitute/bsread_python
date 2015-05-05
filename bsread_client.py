#!/usr/bin/python
import json
import os
import sys
import re


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
        frequency = None

        try:
            if len(line) > 1:
                frequency = float(line[1])

            offset = None
            if len(line) > 2:
                offset = int(line[2])

            configuration.channels.append(Channel(name, frequency=frequency, offset=offset))
        except ValueError:
            print "Frequency (float) or offset (int) specified in wrong type - ignoring channel: "+name

    configuration_string = configuration.json()
    print "Configuration String: "
    print configuration_string

    temporary_file = '.bsread_conf'

    try:
        open(temporary_file, "w").write(configuration_string)
        os.system("/usr/local/epics/base/bin/SL6-x86_64/caput -S "+ioc_name+"-BSREAD:CONFIGURATION $(cat "+temporary_file+" )")
    finally:
        os.remove(temporary_file)


class Configuration:
    def __init__(self):
        self.channels = []

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class Channel:
    def __init__(self, name, frequency=None, offset=None):
        self.name = name
        if frequency is not None:
            self.frequency = frequency
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
    configuration.channels = Channel("name", frequency=100, offset=0)
    configuration.json()

    Usage:
    bsread_client.py [ioc]

    The script reads from standard input and terminates on EOF or empty lines

    An input line looks like this:
    <channel> frequency(optional, type=float ) offset(optional, type=int)
    Note that only the channel name is mandatory.

    Configuration can also be piped from any other process. This is done like this:
    echo -e "one\ntwo\nthree" | python bsread_client.py
    """

    ioc = "PC7920"
    configure_ioc(ioc)