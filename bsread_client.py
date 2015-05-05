#!/usr/bin/python
import json
import os
import sys
import re

# Utility class to generate a bsread configuration string and push it to an IOC


def configure_ioc(ioc_name, input_provider):

    # we use an input_provider class instead of a list of lines as we
    # want to be able to have interactive input as well

    configuration = Configuration()
    input_provider.open()
    while True:
        line = input_provider.read()
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

    input_provider.close()

    configuration_string = json.dumps(configuration, default=lambda o: o.__dict__)
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


class Channel:
    def __init__(self, name, frequency=None, offset=None):
        self.name = name
        if frequency is not None:
            self.frequency = frequency
        if offset is not None:
            self.offset = offset


class InputProvider:

    def __init__(self):
        pass

    def open(self):
        pass

    def read(self):
        # Default implementation
        return sys.stdin.readline()

    def close(self):
        pass


if __name__ == '__main__':
    ioc = "PC7920"
    configure_ioc(ioc, InputProvider())