#!/usr/bin/env python

import bsread
import zmq

if __name__ == "__main__":
    # Startup test sender
    sender = bsread.Bsread(mode=zmq.PUSH)
    sender.connect(address="tcp://*:9999", conn_type="bind", )
    sender.send()
