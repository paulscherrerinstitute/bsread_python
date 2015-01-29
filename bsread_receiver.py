#!/usr/bin/env python

import bsread
import zmq

if __name__ == "__main__":
    # Startup test sender
    bsread = bsread.Bsread(mode=zmq.PULL)
    bsread.connect(address="tcp://localhost:9999", conn_type="connect", )
    while True:
        bsread.receive()
        print "----"
