#!/usr/bin/env python

import bsread
import zmq

if __name__ == "__main__":
    # Startup test sender
    receiver = bsread.Bsread(mode=zmq.PULL)
    receiver.connect(address="tcp://localhost:9999", conn_type="connect", )
    while True:
        print receiver.receive()
