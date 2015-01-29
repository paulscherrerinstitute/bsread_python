#!/usr/bin/env python

import bsread
import zmq

if __name__ == "__main__":
    # Startup test sender
    bsread = bsread.Bsread(mode=zmq.PUSH)
    bsread.connect(address="tcp://*:9999", conn_type="bind", )
    bsread.send()
