import numpy
import bitshuffle
import json
import struct
from collections import OrderedDict

from bsread.data.receiver import get_receive_functions


class Handler:

    def __init__(self):
        self.header_hash = None
        self.receive_functions = None
        self.data_header = None

    def receive(self, receiver):

        # Receive main header
        header = receiver.next(as_json=True)

        message = Message()
        message.pulse_id = header['pulse_id']
        message.hash = header['hash']

        if 'global_timestamp' in header:
            if 'sec' in header['global_timestamp']:
                message.global_timestamp = header['global_timestamp']['sec']
            elif 'epoch' in header['global_timestamp']:
                message.global_timestamp = header['global_timestamp']['epoch']
            else:
                raise RuntimeError("Invalid timestamp format in BSDATA header message {}".format(message))

            message.global_timestamp_offset = header['global_timestamp']['ns']

        # Receiver data header
        if receiver.has_more() and (self.header_hash is None or not self.header_hash == header['hash']):

            self.header_hash = header['hash']

            if 'dh_compression' in header and header['dh_compression'] == 'bitshuffle_lz4':
                data_header_bytes = receiver.next()
                data_header_bytes = numpy.frombuffer(data_header_bytes, dtype=numpy.uint8)
                length = struct.unpack(">q", data_header_bytes[:8].tobytes())[0]
                byte_array = bitshuffle.decompress_lz4(data_header_bytes[12:], shape=(length,),
                                                       dtype=numpy.dtype('uint8'))
                self.data_header = json.loads(byte_array.tobytes().decode())

            else:
                # Interpret data header
                self.data_header = receiver.next(as_json=True)

            # If a message with ho channel information is received,
            # ignore it and return from function with no data.
            if not self.data_header['channels']:
                while receiver.has_more():
                    # Drain rest of the messages - if entering this code there is actually something wrong
                    raw_data = receiver.next()

                return message

            self.receive_functions = get_receive_functions(self.data_header)

            message.format_changed = True
        else:
            # Skip second header
            receiver.next()

        # Receiving data
        counter = 0

        # Todo add some more error checking
        while receiver.has_more():
            raw_data = receiver.next()
            channel_value = Value()

            if raw_data:
                endianness = self.receive_functions[counter][0]["encoding"]
                channel_value.value = self.receive_functions[counter][1].get_value(raw_data, endianness=endianness)

                if receiver.has_more():
                    raw_timestamp = receiver.next()
                    if raw_timestamp:
                        timestamp_array = numpy.fromstring(raw_timestamp, dtype=endianness+'u8')
                        channel_value.timestamp = timestamp_array[0]  # Second past epoch
                        channel_value.timestamp_offset = timestamp_array[1]  # Nanoseconds offset
            else:
                # Consume empty timestamp message
                if receiver.has_more():
                    receiver.next()  # Read empty timestamp message
                channel_value.timestamp = None  # Second past epoch
                channel_value.timestamp_offset = None  # Nanoseconds offset

                # TODO needs to be optimized
            channel_name = self.data_header['channels'][counter]['name']
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
        message = "pulse_id: %d \ndata: " % self.pulse_id + str(self.data)
        return message


class Value:
    def __init__(self, value=None, timestamp=None, timestamp_offset=None):
        self.value = value
        self.timestamp = timestamp
        self.timestamp_offset = timestamp_offset
