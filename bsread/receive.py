#!/usr/bin/env python

import bsread
import zmq


def receive(source, clear=False):
    receiver = bsread.Bsread(mode=zmq.PULL)
    receiver.connect(address=source, conn_type="connect", )

    while True:
        message = receiver.receive()

        # if message_data['header']['pulse_id'] % 10 == 0:
        #     sys.stderr.write("\x1b[2J\x1b[H")

        if clear:
            print(chr(27) + "[2J")

        print message['header']
        if "data_header" in message:
            print message['data_header']
        print message['data']
        print message['timestamp']

        # if "data_header" in message:
        #     print "Data Header: ", message['data_header']
        # print message['data'],  message['timestamp'], message['header']


def main():
    import argparse
    parser = argparse.ArgumentParser(description='BSREAD receive utility')

    parser.add_argument('address', type=str, help='Source address - format "tcp://<address>:<port>"')
    parser.add_argument('-m', '--monitor', action='count', help='Monitor mode / clear the screen on every message')

    arguments = parser.parse_args()
    address = arguments.address

    if arguments.monitor:
        receive(address, clear=True)
    else:
        receive(address)


if __name__ == "__main__":
    main()
