import json

import logging
import numpy

from bsread.data.helpers import get_channel_reader, get_value_reader


class Handler:

    def __init__(self):
        self.data_header_hash = None
        self.data_header = None
        self.channels_definitions = None

    def receive(self, receiver):

        header = receiver.next(as_json=True)

        # We cannot process an empty Header.
        if not header:
            return None

        return_value = {}

        data = []
        timestamp = []
        timestamp_offset = []
        pulse_ids = []
        pulse_id_array = []  # array of all pulse ids

        pulse_id = header['pulse_id']
        pulse_id_array.append(pulse_id)

        if receiver.has_more() and (self.data_header_hash != header['hash']):

            self.data_header_hash = header['hash']

            # Read the data header.
            data_header_bytes = receiver.next()
            data_header = json.loads(get_value_reader("string", header.get('dh_compression'))(data_header_bytes))

            # If a message with ho channel information is received,
            # ignore it and return from function with no data.
            if not data_header['channels']:

                logging.warning("Received message without channels.")

                while receiver.has_more():
                    receiver.next()

                return_value['header'] = header
                return_value['pulse_id_array'] = pulse_id_array

                return_value['data'] = 'No channel'
                return_value['timestamp'] = None
                return_value['timestamp_offset'] = None
                return_value['pulse_ids'] = None

                return return_value

            # TODO: Why do we need to pre-process the message? Source change?
            for channel in data_header['channels']:
                # Define endianness of data
                # > - big endian
                # < - little endian (default)
                channel["encoding"] = '>' if channel.get("encoding") == "big" else '<'

            # Construct the channel definitions.
            self.channels_definitions = [(channel["name"], channel["encoding"], get_channel_reader(channel))
                                         for channel in data_header['channels']]

            self.data_header = data_header
        else:
            # Skip second header
            receiver.next()

        # The data header should be added to every message.
        return_value['data_header'] = self.data_header

        # Receiving data
        counter = 0
        # msg_data_size = 0
        while receiver.has_more():
            channel_name, channel_endianness, channel_reader = self.channels_definitions[counter]

            raw_data = receiver.next()

            if raw_data:
                pulse_ids.append(pulse_id)

                data.append(channel_reader(raw_data))

                if receiver.has_more():

                    raw_timestamp = receiver.next()

                    if raw_timestamp:
                        timestamp_array = numpy.frombuffer(raw_timestamp, dtype=channel_endianness + 'u8')
                        timestamp.append(timestamp_array[0])  # Second past epoch
                        timestamp_offset.append(timestamp_array[1])  # Nanoseconds offset
            else:
                if receiver.has_more():
                    receiver.next()  # Read empty timestamp message

                data.append(None)
                timestamp.append(None)
                timestamp_offset.append(None)
                pulse_ids.append(None)

            counter += 1

        # Todo need to add some more error checking

        return_value['header'] = header
        return_value['pulse_id_array'] = pulse_id_array

        return_value['data'] = data
        return_value['timestamp'] = timestamp
        return_value['timestamp_offset'] = timestamp_offset
        return_value['pulse_ids'] = pulse_ids
        # return_value['size'] = msg_data_size

        return return_value
