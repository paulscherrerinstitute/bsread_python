#!/usr/bin/env python


import zmq
import struct

context = zmq.Context.instance()

socket = context.socket(zmq.PULL)
socket.connect('tcp://localhost:9999')

while True:
    print socket.recv()  # Main header
    print socket.recv()  # Data header
    while socket.getsockopt(zmq.RCVMORE):
        raw_data = socket.recv()
        if raw_data :
            data = struct.unpack('d', raw_data)
            print data
    print '----'


    ## value = array.array('d',message)
    # value.byteswap() # if different endianness
    ## print value