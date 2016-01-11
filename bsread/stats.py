import mflow
from .handlers.bsr_m_1_0 import Handler
import zmq
import time
import datetime
import argparse
import logging

logger = logging.getLogger(__name__)

message_print_format = "{:40.40}| {:25.25} {:30.30}"

previous_pulse_id = 0
first_iteration = True
data_header = None


def print_message_data(message_data):

    global first_iteration
    global data_header

    # Print header
    print(message_print_format.format("NAME", "VAL", "TIMESTAMP"))
    print("_"*80)

    if first_iteration and 'data_header' in message_data:
        data_header = message_data['data_header']
        first_iteration = False

    global_timestamp = message_data['header']['global_timestamp']['epoch']
    global_timestamp_ns = message_data['header']['global_timestamp']['ns']
    pulse_id = message_data['header']['pulse_id']

    try:
        date_g = datetime.datetime.fromtimestamp(global_timestamp + float(global_timestamp_ns)/1e9)
    except:
        date_g = 'None'

    # Print values
    for i, c in enumerate(data_header['channels']):
        channel_name = c['name']
        channel_value = message_data['data'][i]
        # pulse_id = message_data['pulse_ids'][i]
        timestamp = message_data['timestamp'][i]
        timestamp_ns = message_data['timestamp_offset'][i]
        # global_timestamp = message_data['header']['global_timestamp']['epoch']
        # global_timestamp_ns = message_data['header']['global_timestamp']['ns']

        try:
            date = datetime.datetime.fromtimestamp(timestamp + float(timestamp_ns)/1e9)
            # date_g = datetime.datetime.fromtimestamp(global_timestamp + float(global_timestamp_ns)/1e9)
        except:
            date = 'None'
            # date_g = 'None'

        print(message_print_format.format(channel_name, str(channel_value), str(date)))

    print("_"*80)

    # Print "global" metadata
    print("pulse_id: %d" % pulse_id)
    print("global_timestamp: %s" % str(date_g))


def data_consistency_check(message_data):
    """
    Check 'consistency' of messages, i.e. whether pulse_id increases by one
    Args:
        message_data: Current message

    Returns: Messages missed between last and current message - i.e. lost/missed messages

    """
    global previous_pulse_id
    current_pulse_id = message_data['header']['pulse_id']

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
    from .cli_utils import EnvDefault
    parser = argparse.ArgumentParser(description='BSREAD receiving utility')

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
    messages_missed = 0

    previous_time = time.time()
    previous_total_bytes_received = 0

    while True:

        message = receiver.receive(handler=handler.receive)
        total_bytes_received = message.statistics.total_bytes_received

        # Check consistency
        messages_missed += data_consistency_check(message.data)

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
            print("Messages Missed: {} ".format(messages_missed))
        messages_received += 1

if __name__ == "__main__":
    main()
