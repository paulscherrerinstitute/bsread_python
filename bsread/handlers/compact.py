import json
import logging
from collections import OrderedDict

import numpy as np

from bsread.data.helpers import get_channel_reader, get_value_reader


class Handler:
    def __init__(self):
        # Used for detecting if the data header has changed - we need to reconstruct the channel definitions.
        self.data_header_hash = None
        self.channels_definitions = None

    def receive(self, receiver):

        # Receive main header
        header = receiver.next(as_json=True)

        # We cannot process an empty Header.
        if not header:
            return None

        message = Message()
        message.pulse_id = header["pulse_id"]
        message.hash = header["hash"]

        if "global_timestamp" in header:
            if "sec" in header["global_timestamp"]:
                message.global_timestamp = header["global_timestamp"]["sec"]
            elif "epoch" in header["global_timestamp"]:
                message.global_timestamp = header["global_timestamp"]["epoch"]
            else:
                raise RuntimeError(f"Invalid timestamp format in BSDATA header message {message}")

            message.global_timestamp_offset = header["global_timestamp"]["ns"]

        # Receiver data header, check if header has changed - and in this case recreate the channel definitions.
        if receiver.has_more() and (self.data_header_hash != header["hash"]):
            # Set the current header hash as the new hash.
            self.data_header_hash = header["hash"]

            # Read the data header.
            data_header_bytes = receiver.next()
            data_header = json.loads(get_value_reader("string", header.get("dh_compression"),
                                                      value_name="data_header")(data_header_bytes))

            # If a message with ho channel information is received,
            # ignore it and return from function with no data.
            if not data_header["channels"]:
                logging.warning("Received message without channels.")
                while receiver.has_more():
                    # Drain rest of the messages - if entering this code there is actually something wrong
                    receiver.next()

                return message

            # TODO: Why do we need to pre-process the message? Source change?
            for channel in data_header["channels"]:
                # Define endianness of data
                # > - big endian
                # < - little endian (default)
                channel["encoding"] = ">" if channel.get("encoding") == "big" else "<"

            # Construct the channel definitions.
            self.channels_definitions = [(channel["name"], channel["encoding"], get_channel_reader(channel))
                                         for channel in data_header["channels"]]

            # Signal that the format has changed.
            message.format_changed = True
        else:
            # Skip second header - we already have the receive functions setup.
            receiver.next()

        # Receiving data
        counter = 0

        # Todo add some more error checking
        while receiver.has_more():
            channel_name, channel_endianness, channel_reader = self.channels_definitions[counter]

            raw_data = receiver.next()
            channel_value = Value()

            if raw_data:
                channel_value.value = channel_reader(raw_data)

                if receiver.has_more():

                    raw_timestamp = receiver.next()

                    if raw_timestamp:
                        timestamp_array = np.frombuffer(raw_timestamp, dtype=channel_endianness + "u8")
                        channel_value.timestamp = timestamp_array[0]  # Second past epoch
                        channel_value.timestamp_offset = timestamp_array[1]  # Nanoseconds offset
            else:
                # Consume empty timestamp message
                if receiver.has_more():
                    receiver.next()  # Read empty timestamp message

            message.data[channel_name] = channel_value
            counter += 1

        return message


class Message:
    def __init__(self, pulse_id=None, global_timestamp=None, global_timestamp_offset=None, hash=None, data=None):
        self.pulse_id = pulse_id
        self.global_timestamp = global_timestamp
        self.global_timestamp_offset = global_timestamp_offset
        self.hash = hash
        if data:
            self.data = data  # Dictionary of values
        else:
            self.data = OrderedDict()

        self.format_changed = False

    def __str__(self):
        message = f"pulse_id: {self.pulse_id} \ndata: {self.data}"
        return message


class Value:
    def __init__(self, value=None, timestamp=None, timestamp_offset=None):
        self.value = value
        self.timestamp = timestamp
        self.timestamp_offset = timestamp_offset
