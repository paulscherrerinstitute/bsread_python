#!/usr/bin/env python

import bsread
import zmq


if __name__ == "__main__":
    receiver = bsread.Bsread(mode=zmq.PULL)
    # receiver.connect(address="tcp://gfa-lc6-64:9999", conn_type="connect", )
    receiver.connect(address="tcp://localhost:9999", conn_type="connect", )

    while True:
        message_data = receiver.receive()
        if "data_header" in message_data:
            print "Data Header: ", message_data['data_header']
        print message_data['data'],  message_data['timestamps'], message_data['header']

