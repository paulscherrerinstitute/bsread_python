import mflow
from .handlers.compact import Handler
import zmq
import time
import datetime
import argparse
import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

message_print_format = "{:40.40}| {:25.25} {:30.30}"

previous_pulse_id = 0


class Statistics:
    def __init__(self):
        self.missed_pulse_ids = 0
        self.duplicated_pulse_ids = 0
        self.reverted_pulse_ids = 0


def print_message_data(message_data):

    # Print header
    print(message_print_format.format("NAME", "VAL", "TIMESTAMP"))
    print("_"*80)

    global_timestamp = message_data.global_timestamp
    global_timestamp_ns = message_data.global_timestamp_offset
    pulse_id = message_data.pulse_id

    try:
        date_g = datetime.datetime.fromtimestamp(global_timestamp + float(global_timestamp_ns)/1e9)
    except:
        date_g = 'None'

    # Print values
    for i, c in message_data.data.items():
        channel_name = i
        channel_value = c.value
        timestamp = c.timestamp
        timestamp_ns = c.timestamp_offset

        try:
            date = datetime.datetime.fromtimestamp(timestamp + float(timestamp_ns)/1e9)
        except:
            date = 'None'

        print(message_print_format.format(channel_name, str(channel_value), str(date)))

    print("_"*80)

    # Print "global" metadata
    print("pulse_id: %d" % pulse_id)
    print("global_timestamp: %s" % str(date_g))


def data_consistency_check(message_data, statistics):
    """
    Check 'consistency' of messages, i.e. whether pulse_id increases by one
    Args:
        message_data: Current message
        statistics: Current statistics

    Returns: Metadata regarding messages missed between last and current message - i.e. lost/missed messages etc.

    """
    global previous_pulse_id
    current_pulse_id = message_data.pulse_id

    if not previous_pulse_id:
        previous_pulse_id = current_pulse_id
    elif previous_pulse_id + 1 != current_pulse_id:
        if current_pulse_id == previous_pulse_id:
            statistics.duplicated_pulse_ids += 1
        elif current_pulse_id > previous_pulse_id:
            logger.warning("Skipped message detected, expected {} but received {}".format(previous_pulse_id + 1, current_pulse_id))
            statistics.missed_pulse_ids = current_pulse_id - previous_pulse_id - 1
            previous_pulse_id = current_pulse_id
        else:
            # current pulse id is smaller than previous one
            statistics.reverted_pulse_ids += 1
    else:
        previous_pulse_id = current_pulse_id


def main():

    # Argument parsing
    from .cli_utils import EnvDefault
    parser = argparse.ArgumentParser(description='bsread statistics utility')

    parser.add_argument('-s', '--source', action=EnvDefault, envvar='BS_SOURCE', type=str,
                        help='source address, has to be in format "tcp://<address>:<port>"')
    parser.add_argument('-m', '--monitor', action='count',
                        help='Enable monitor mode, this will clear the screen on every message to allow easier monitoring.')
    parser.add_argument('-n', default=1, type=int,
                        help='Limit message printing to every n messages, this will reduce CPU load. Note that all messages are still received, but are not displayed. If -n 0 is passed message display is disabled')
    parser.add_argument('-l', '--log', type=str,
                        help='Enable logging. All errors (pulse_id skip, etc..) will be logged in file specified')
    parser.add_argument('-v', '--value', action='count', help='Display values')

    # Parse arguments
    arguments = parser.parse_args()
    address = arguments.source

    import re
    if not re.match('^tcp://', address):
        print('Protocol not defined for address - Using tcp://')
        address = 'tcp://' + address
    if not re.match('.*:[0-9]+$', address):
        print('Port not defined for address - Using 9999')
        address += ':9999'
    if not re.match('^tcp://[a-zA-Z\.\-0-9]+:[0-9]+$', address):
        print('Invalid URI - ' + address)
        exit(-1)

    if arguments.log:
        handler = logging.FileHandler(arguments.log)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    logger.info("Connecting to {} type PULL".format(address))
    receiver = mflow.connect(address, conn_type="connect", mode=zmq.PULL)
    handler = Handler()
    logger.info("Connection opened")

    messages_received = 0
    previous_messages_received = 0
    statistics = Statistics()

    previous_time = time.time()
    previous_total_bytes_received = 0

    while True:

        message = receiver.receive(handler=handler.receive)
        total_bytes_received = message.statistics.total_bytes_received

        # Check consistency
        data_consistency_check(message.data, statistics)

        if arguments.n != 0 and (messages_received % arguments.n) == 0:

            if arguments.monitor:
                print(chr(27) + "[2J")

            if arguments.value:
                print_message_data(message.data)

            now = time.time()
            delta_time = now - previous_time

            # Calculations
            receive_rate = (total_bytes_received - previous_total_bytes_received) / delta_time
            message_rate = (messages_received - previous_messages_received) / delta_time

            previous_total_bytes_received = total_bytes_received
            previous_messages_received = messages_received
            previous_time = now

            print("_"*80)
            print("Messages Received: {}".format(messages_received))
            print("Message Rate: {} Hz".format(message_rate))
            print("Data Received: {} Mb".format(total_bytes_received/1024.0/1024.0))
            print("Receive Rate: {} Mbps".format(receive_rate/1024/1024*8))
            print("Missed Pulse_IDs: {} ".format(statistics.missed_pulse_ids))
            print("Duplicated Pulse_IDs: {} ".format(statistics.duplicated_pulse_ids))
            print("Reverted Pulse_IDs: {} ".format(statistics.reverted_pulse_ids))
        messages_received += 1

if __name__ == "__main__":
    main()
