import bsread
import zmq
import time
import datetime
import argparse


message_print_format = "{:30.30}| {:25.25} [{:7.7}] {:20.20}"
log_print_format = "{timestamp:20.20}: {msg}"
log_file = None

def bsread_util_log(message):
    log = log_print_format.format(timestamp=str(datetime.datetime.now()),msg=message)
    print log

    if(log_file):
        log_file.write(log+'\n')

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
        bsread_util_log("Skipped message detected, expecteted {} but received {}".format(last_id+1, current_id))
        last_id = 0 ##Reset last id        
        return False

    last_id = current_id

    return True


if __name__ == "__main__":

    # Argument parsing

    parser = argparse.ArgumentParser(description='BSREAD receiving utility')

    parser.add_argument(
        'address', type=str, help='source address, has to be in format "tcp://<address>:<port>"')
    parser.add_argument('-m', '--monitor', action='count',
                        help='Enable monitor mode, this will clear the screen on every message to allow easier monitoring.')
    parser.add_argument('-n', default=1, type=int,
                        help='Limit message priniting to every n messages, this will reduce CPU load. Note that all messages are still recevied, but are not displayed. If -n 0 is passed message display is disabled')
    parser.add_argument('-l', '--log', type=str,
                    help='Enable logging. All errors (BunchID cnt skip, etc..) will be logged in file specifed')


    args = parser.parse_args()
    
    address = args.address


    if args.log:
        bsread_util_log("Opening log file {}".format(args.log))
        log_file= open(args.log,'a+')

    bsread_util_log("Connecting to {} type PULL".format(address))
    receiver = bsread.Bsread(mode=zmq.PULL)
    receiver.connect(address=address, conn_type="connect", )
    bsread_util_log("Connection opened")

    i = 0

    #Bandwitdh calcucaltions
    time_bw = time.time()
    received_bw = 0
    i_prev = 0
    while True:

        message = receiver.recive_message()

        consistency_check(message)
            

        if( args.n != 0 and (i % args.n) == 0):
            print_message(message, args.monitor)

            if(args.monitor):
                now = time.time()
                rx_bw = (receiver.received_b - received_bw) / (now - time_bw)
                message_rate = (i - i_prev) / (now - time_bw)

                time_bw = now
                received_bw = receiver.received_b
                i_prev = i

                print("_"*90)
                print("STATS:\n")
                print("Received {} messages".format(i))
                print("Avg message rate {} Hz".format(message_rate))
                print("Received {} Mb of payload data".format(receiver.received_b/1024/1024))
                print("Received rate {} Mbps".format(rx_bw/1024/1024*8))


        i = i+1


    bsread_util_log("Shutting down!")
