import bsread
import zmq
import datetime
import argparse


message_print_format = "{:30.30}| {:25.25} [{:7.7}] {:20.20}"


def print_header(clear=True):
    if(clear):
        print(chr(27) + "[2J")

    print(message_print_format.format("NAME", "VAL", "PULSEID", "TIMESTAMP"))
    print("_"*90)


def print_message(message, clear=True):

    if(clear):
        print_header(True)

    for c in message.itervalues():

        # Check if the message data is scalar
        l = 1
        if hasattr(c.val, "__len__"):
            l = len(c.val)

        # Format timestamp
        if c.timestamp != None:
            date = datetime.datetime.fromtimestamp(c.timestamp)
        else:
            date = "None"

        print message_print_format.format(c.name, str(c.val), str(c.pulseid), str(date))


last_id = 0


def consistency_check(message):
    global last_id
    current_id = message.items()[0][1].pulseid

    if not last_id:
        last_id = current_id
        return True

    if last_id + 1 != current_id:
        print "Skipped message detected, expecteted {} but received {}".format(last_id+1, current_id)
        return False

    last_id = current_id

    return True


if __name__ == "__main__":

    # Argument parsing

    parser = argparse.ArgumentParser(description='BSREAD receiving utility')

    parser.add_argument(
        'address', type=str, help='source address, has to be in format "tcp://<address>:<port>"')
    parser.add_argument('-c', '--check', action='count',
                        help='Enable consistency checking. This will stop the program if received pulse_id is not monotonically increasing')
    parser.add_argument('-m', '--monitor', action='count',
                        help='Enable monitor mode, this will clear the screen on every message to allow easier monitoring.')
    parser.add_argument('-n', default=1, type=int,
                        help='Limit message priniting to every n messages, this will reduce CPU load. Note that all messages are still recevied, but are not displayed')

    args = parser.parse_args()

    address = args.address

    receiver = bsread.Bsread(mode=zmq.PULL)
    receiver.connect(address=address, conn_type="connect", )

    i = 0
    while True:

        message = receiver.recive_message()

        if(args.check):
            if not consistency_check(message):
                break

        if (i % args.n) == 0:
            print_message(message, args.monitor)

        i = i+1
