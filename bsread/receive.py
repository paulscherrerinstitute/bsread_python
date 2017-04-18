import mflow
# from .handlers.bsr_m_1_0 import Handler
from .handlers.compact import Handler
from . import dispatcher
import zmq
import numpy


def receive(source=None, clear=False, queue_size=100, mode=zmq.PULL):
    numpy.set_printoptions(threshold=5)
    numpy.set_printoptions(linewidth=100)

    print('Trying to connect to %s' % source)

    receiver = mflow.connect(source, conn_type="connect", queue_size=queue_size, mode=mode)
    handler = Handler()

    while True:
        message = receiver.receive(handler=handler.receive)
        message = message.data  # As the rest of the code is only interested in the message data, not statistics

        # if message_data['header']['pulse_id'] % 10 == 0:
        #     sys.stderr.write("\x1b[2J\x1b[H")

        if clear:
            print((chr(27) + "[2J"))

        separator = '\t'
        # separator = ', '

        if message.format_changed or clear:
            # Have pulse_id, ... in first column
            keys = "pulse_id" + separator + "global_timestamp" + separator + "global_timestamp_offset"

            for key in message.data.keys():
                if keys:
                    keys = keys + separator + key
                else:
                    keys = key
            print(keys)

        # pprint.pprint(message.data.values())
        # Have pulse_id in first column
        values = str(message.pulse_id) + separator + str(message.global_timestamp) + separator + str(message.global_timestamp_offset)
        for value in message.data.values():
            if values:
                values = values + separator + str(value.value)
            else:
                values = str(value.value)

        print(values)


def main():
    import sys
    import argparse
    parser = argparse.ArgumentParser(description='bsread receive utility')

    parser.add_argument('-s', '--source', default=None, type=str,
                        help='Source address - format "tcp://<address>:<port>"')
    parser.add_argument('-c', '--clear', action='count', help='Monitor mode / clear the screen on every message')
    parser.add_argument('-m', '--mode', default='pull', choices=['pull', 'sub'], type=str,
                        help='Communication mode - either pull or sub (default depends on the use of -s option)')
    parser.add_argument('-q', '--queue', default=100, type=int,
                        help='Queue size of incoming queue (default = 100)')

    parser.add_argument('channel', type=str, nargs='*',
                        help='Channels to retrieve (from dispatching layer)')

    arguments = parser.parse_args()
    address = arguments.source  # Either use dispatcher or environment variables
    channels = arguments.channel
    clear = arguments.clear
    queue_size = arguments.queue

    mode = mflow.SUB if arguments.mode == 'sub' else mflow.PULL
    use_dispatching = False

    if not channels and not address:
        print('\nNo source nor channels are specified - exiting!\n')
        parser.print_help()
        sys.exit(-1)

    if address:
        import re
        if not re.match('^tcp://', address):
            # print('Protocol not defined for address - Using tcp://')
            address = 'tcp://' + address
        if not re.match('.*:[0-9]+$', address):
            # print('Port not defined for address - Using 9999')
            address += ':9999'
        if not re.match('^tcp://[a-zA-Z.\-0-9]+:[0-9]+$', address):
            print('\nInvalid URI - %s\n' % address)

            sys.exit(-1)
    else:
        # Connect via the dispatching layer
        use_dispatching = True
        address = dispatcher.request_stream(channels)
        mode = zmq.SUB

    try:
        receive(source=address, clear=clear, queue_size=queue_size, mode=mode)

    except AttributeError:
        # Usually AttributeError is thrown if the receiving is terminated via ctrl+c
        # As we don't want to see a stacktrace then catch this exception
        pass
    finally:
        if use_dispatching:
            print('Closing stream')
            dispatcher.remove_stream(address)


if __name__ == "__main__":
    main()
