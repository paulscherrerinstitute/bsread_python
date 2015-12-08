import bsread
import zmq
import time
import datetime
import argparse
import logging

logger = logging.getLogger(__name__)

message_print_format = "{:30.30}| {:25.25} [{:7.7}] {:20.20}"

previous_pulse_id = 0


def print_header(clear=True):
    if clear:
        print(chr(27) + "[2J")

    print(message_print_format.format("NAME", "VAL", "PULSEID", "TIMESTAMP"))
    print("_"*90)


def print_message(message, clear=True):

    if clear:
        print_header(True)

    for c in message.itervalues():

        # Array/Waveform handling
        # Check if the message data is scalar
        # l = 1
        # if hasattr(c.val, "__len__"):
        #     l = len(c.val)

        # Format timestamp
        if c.timestamp is not None:
            try:
                date = datetime.datetime.fromtimestamp(c.timestamp)
            except:
                date = "None"
        else:
            date = "None"

        print message_print_format.format(c.name, str(c.val), str(c.pulseid), str(date))


def consistency_check(message):
    """
    Check 'consistency' of messages, i.e. whether pulse_id increases by one
    Args:
        message: Current message

    Returns: Messages missed between last and current message - i.e. lost/missed messages

    """
    global previous_pulse_id
    current_pulse_id = message.items()[0][1].pulseid

    messages_missed = 0

    if not previous_pulse_id:
        pass
    elif previous_pulse_id + 1 != current_pulse_id:
        logger.warning("Skipped message detected, expected {} but received {}".format(previous_pulse_id + 1, current_pulse_id))
        messages_missed = current_pulse_id - previous_pulse_id - 1

    previous_pulse_id = current_pulse_id
    return messages_missed


def main():

    # Argument parsing
    from cli_utils import EnvDefault
    parser = argparse.ArgumentParser(description='BSREAD receiving utility')

    parser.add_argument('-s', '--source', action=EnvDefault, envvar='BS_SOURCE', type=str,
                        help='source address, has to be in format "tcp://<address>:<port>"')
    parser.add_argument('-m', '--monitor', action='count',
                        help='Enable monitor mode, this will clear the screen on every message to allow easier monitoring.')
    parser.add_argument('-n', default=1, type=int,
                        help='Limit message printing to every n messages, this will reduce CPU load. Note that all messages are still received, but are not displayed. If -n 0 is passed message display is disabled')
    parser.add_argument('-l', '--log', type=str,
                        help='Enable logging. All errors (pulse_id skip, etc..) will be logged in file specified')

    # Parse arguments
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

    if arguments.log:
        handler = logging.FileHandler(arguments.log)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    logger.info("Connecting to {} type PULL".format(address))
    receiver = bsread.Bsread(mode=zmq.PULL)
    receiver.connect(address=address, conn_type="connect", )
    logger.info("Connection opened")

    messages_received = 0
    previous_messages_received = 0
    messages_missed = 0

    previous_time = time.time()
    previous_total_bytes_received = 0

    while True:

        message = receiver.recive_message()
        total_bytes_received = receiver.received_b

        # Check consistency
        messages_missed += consistency_check(message)

        if arguments.n != 0 and (messages_received % arguments.n) == 0:

            print_message(message, arguments.monitor)

            if arguments.monitor:
                now = time.time()
                delta_time = now - previous_time

                # Calculations
                receive_rate = (total_bytes_received - previous_total_bytes_received) / delta_time
                message_rate = (messages_received - previous_messages_received) / delta_time

                previous_total_bytes_received = total_bytes_received
                previous_messages_received = messages_received
                previous_time = now

                print("_"*90)
                print("STATS:\n")
                print("Messages Received: {}".format(messages_received))
                print("Message Rate: {} Hz".format(message_rate))
                print("Data Received: {} Mb".format(total_bytes_received/1024.0/1024.0))
                print("Receive Rate: {} Mbps".format(receive_rate/1024/1024*8))
                print("Messages Missed: {} ".format(messages_missed))
        messages_received += 1

if __name__ == "__main__":
    main()
