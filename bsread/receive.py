import mflow
from handlers.bsr_m_1_0 import Handler
import zmq


def receive(source, clear=False):
    receiver = mflow.connect(source, conn_type="connect", mode=zmq.PULL)
    handler = Handler()

    while True:
        message = receiver.receive(handler=handler.receive)
        message = message.data  # As the rest of the code is only interested in the message data, not statistics

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
    from cli_utils import EnvDefault
    import argparse
    parser = argparse.ArgumentParser(description='bsread receive utility')

    parser.add_argument('-s', '--source', action=EnvDefault, envvar='BS_SOURCE', type=str, help='Source address - format "tcp://<address>:<port>"')
    parser.add_argument('-m', '--monitor', action='count', help='Monitor mode / clear the screen on every message')

    arguments = parser.parse_args()
    address = arguments.source

    import re
    if not re.match('^tcp://', address):
        print 'Protocol not defined for address - Using tcp://'
        address = 'tcp://' + address
    if not re.match('.*:[0-9]+$', address):
        print 'Port not defined for address - Using 9999'
        address += ':9999'
    if not re.match('^tcp://[a-zA-Z\.\-0-9]+:[0-9]+$', address):
        print 'Invalid URI - ' + address
        exit(-1)

    if arguments.monitor:
        receive(address, clear=True)
    else:
        receive(address)


if __name__ == "__main__":
    main()
