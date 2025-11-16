import re
import sys
import time

import zmq

from bsread import Source, dispatcher


def pollStream(pattern, timeout):
    ch_names = []
    ch_values = {}
    messages = 0
    try:
        channels = dispatcher.get_current_channels()
        for channel in channels:
            if re.match(pattern, channel["name"]):
                ch_names.append(channel["name"])
                ch_values[channel["name"]] = None


        in_stream = Source(channels=ch_names, queue_size=1, receive_timeout=100)
        in_stream.connect()
        in_stream.stream.receiver.socket.setsockopt(zmq.LINGER, 0)
#        print(f"Created stream {in_stream.stream.address}\n")

        time_start = time.time()
        try:
            while True:
                #message = in_stream.receive(block=False)
                message = in_stream.receive()
                messages += 1

                try:
                    for ch_name in message.data.data.keys():
                        ch_values[ch_name] = message.data.data[ch_name].value
                except:
                    pass

                got_all_data = True
                for ch_nm, ch_vl in ch_values.items():
                    #got_all_data = got_all_data and ch_vl is not None
                    if ch_vl is None:
                        got_all_data = False
                        break
                if got_all_data:
                    time_total = time.time() - time_start
                    print(f"\nBeam-synchronous data available after {time_total:.1f} seconds and {messages} messages")
                    break
                if timeout > 0 and (time.time()-time_start) > timeout:
                    print("\nTimeout, unable to retrieve beam-synchronous data!\nMissing channels:")
                    for ch_nm, ch_vl in ch_values.items():
                        if ch_vl is None:
                            print()
                            print(ch_nm)
                            print()
                    break

#                time.sleep(interval)
#                in_stream.stream.receiver.flush(True)
#                in_stream.stream.receiver.socket.disconnect(in_stream.stream.address)
#                in_stream.stream.receiver.socket.connect(in_stream.stream.address)

        except KeyboardInterrupt:
            pass

        try:
            in_stream.disconnect()
            dispatcher.remove_stream(in_stream.address)
        except:
            pass

    except Exception as e:
        print(f"Unable to retrieve channels\nReason:\n{e}", file=sys.stderr)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Confirm availability of beam-synchronous channels")

    parser.add_argument("pattern", type=str, nargs="?", help="Regex channel pattern")
    parser.add_argument("-t", "--timeout", default=0, type=int, help="Timeout in seconds")

    arguments = parser.parse_args()

    pattern = arguments.pattern
    if not pattern:
        pattern = ".*"
    pattern = ".*" + pattern + ".*"

    pollStream(pattern, arguments.timeout)





if __name__ == "__main__":
    main()



