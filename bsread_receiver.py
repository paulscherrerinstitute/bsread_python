#!/usr/bin/env python

import bsread
import zmq


def receive(source):
    receiver = bsread.Bsread(mode=zmq.PULL)
    receiver.connect(address=source, conn_type="connect", )

    while True:
        message_data = receiver.receive()
        if "data_header" in message_data:
            print "Data Header: ", message_data['data_header']
        print message_data['data'],  message_data['timestamps'], message_data['header']


if __name__ == "__main__":
    import sys
    import getopt

    source_ = 'tcp://localhost:9999'  # 'tcp://gfa-lc6-64:9999'

    arguments = sys.argv[1:]
    usage = sys.argv[0]+' -s <source>'

    try:
        opts, args = getopt.getopt(arguments, "hs:", ["source="])
    except getopt.GetoptError:
        print usage
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print usage
            sys.exit()
        elif opt in ("-s", "--source"):
            source_ = arg

    receive(source_)