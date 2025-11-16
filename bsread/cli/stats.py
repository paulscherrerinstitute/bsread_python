import datetime
import logging
import time

import click
import mflow

from bsread import dispatcher
from bsread.handlers.compact import Handler
from .utils import check_and_update_uri, get_base_url


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
        date_g = "None"

    # Print values
    for i, c in message_data.data.items():
        channel_name = i
        channel_value = c.value
        timestamp = c.timestamp
        timestamp_ns = c.timestamp_offset

        try:
            date = datetime.datetime.fromtimestamp(timestamp + float(timestamp_ns)/1e9)
        except:
            date = "None"

        print(message_print_format.format(channel_name, str(channel_value), str(date)))

    print("_"*80)

    # Print "global" metadata
    print(f"pulse_id: {pulse_id}")
    print(f"global_timestamp: {date_g}")


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
            logger.warning("Skipped message detected, expected {} but received {}".format(
                previous_pulse_id + 1, current_pulse_id))

            statistics.missed_pulse_ids += current_pulse_id - previous_pulse_id - 1
            previous_pulse_id = current_pulse_id

        else:
            # current pulse id is smaller than previous one
            statistics.reverted_pulse_ids += 1
    else:
        previous_pulse_id = current_pulse_id


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("channels", default=None, type=str, nargs=-1)
@click.option("-s", "--source", default=None, type=str, help="Source address - format 'tcp://<address>:<port>'")
@click.option("-m", "--mode", default="sub",
              type=click.Choice(["pull", "sub"], case_sensitive=False),
              help="Communication mode - either pull or sub (default depends on the use of -s option)")
@click.option("--clear", default=False, is_flag=True, help="Monitor mode / clear the screen on every message")
@click.option("-q", "--queue", "queue_size", default=100, type=int, help="Queue size of incoming queue")
@click.option("--base_url", default=None, help="URL of dispatcher")
@click.option("--backend", default=None, help="Backend to query")
@click.option("-l", "--log", "logfile", type=str,
              help="Enable logging. All errors (pulse_id skip, etc..) will be logged in file specified")
@click.option("-v", "--value", "show_values", default=False, is_flag=True, help="Display values")
@click.option("-n", "show_nth_value", default=100, type=int,
              help="Limit message printing to every n messages, this will reduce CPU load. Note that all "
                   "messages are still received, but are not displayed. If -n 0 is passed message "
                   "display is disabled")
def stats(channels, source, mode, clear, queue_size, base_url, backend, logfile, show_values, show_nth_value):

    base_url = get_base_url(base_url, backend)

    use_dispatching = False
    mode = mflow.SUB if mode == "sub" else mflow.PULL

    if not channels and source is None:
        raise click.BadArgumentUsage("No source or channels are specified")

    if source:
        source = check_and_update_uri(source, exception=click.BadArgumentUsage)
    else:
        # Connect via the dispatching layer
        use_dispatching = True
        source = dispatcher.request_stream(channels, base_url=base_url)
        mode = mflow.SUB

    if logfile:
        handler = logging.FileHandler(logfile)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    logger.info(f"Connecting to {source}")
    receiver = mflow.connect(source, conn_type="connect", queue_size=queue_size, mode=mode)
    handler = Handler()
    logger.info("Connection opened")

    messages_received = 0
    previous_messages_received = 0
    statistics = Statistics()

    previous_time = time.time()
    previous_total_bytes_received = 0

    try:
        while True:

            message = receiver.receive(handler=handler.receive)
            total_bytes_received = message.statistics.total_bytes_received

            # Check consistency
            data_consistency_check(message.data, statistics)

            if show_nth_value != 0 and (messages_received % show_nth_value) == 0:

                if clear:
                    print(chr(27) + "[2J")

                if show_values:
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
                print(f"Messages Received: {messages_received}")
                print(f"Message Rate: {message_rate} Hz")
                print(f"Data Received: {total_bytes_received/1024.0/1024.0} Mb")
                print(f"Receive Rate: {receive_rate/1024/1024*8} Mbps")
                print(f"Missed Pulse_IDs: {statistics.missed_pulse_ids} ")
                print(f"Duplicated Pulse_IDs: {statistics.duplicated_pulse_ids} ")
                print(f"Reverted Pulse_IDs: {statistics.reverted_pulse_ids} ")
            messages_received += 1

    except KeyboardInterrupt:
        # KeyboardInterrupt is thrown if the receiving is terminated via ctrl+c
        # As we don't want to see a stacktrace then catch this exception
        print() # print ^C on its own line
    finally:
        if use_dispatching:
            print("Closing stream")
            dispatcher.remove_stream(source, base_url=base_url)


def main():
    stats()





if __name__ == "__main__":
    main()



