import numpy
import json
import bitshuffle
import struct

from bsread.data.receiver import get_receive_functions


class Handler:

    def __init__(self):
        self.header_hash = None
        self.receive_functions = None

    def receive(self, receiver):

        header = receiver.next(as_json=True)

        return_value = {}

        data = []
        timestamp = []
        timestamp_offset = []
        pulse_ids = []
        pulse_id_array = []  # array of all pulse ids

        pulse_id = header['pulse_id']
        pulse_id_array.append(pulse_id)

        if receiver.has_more() and (self.header_hash is None or not self.header_hash == header['hash']):

            self.header_hash = header['hash']

            if 'dh_compression' in header and header['dh_compression'] == 'bitshuffle_lz4':
                data_header_bytes = receiver.next()
                data_header_bytes = numpy.frombuffer(data_header_bytes, dtype=numpy.uint8)
                length = struct.unpack(">q", data_header_bytes[:8].tobytes())[0]
                byte_array = bitshuffle.decompress_lz4(data_header_bytes[12:], shape=(length,),
                                                       dtype=numpy.dtype('uint8'))
                data_header = json.loads(byte_array.tobytes().decode())
            else:
                # Interpret data header
                data_header = receiver.next(as_json=True)

            # If a message with ho channel information is received,
            # ignore it and return from function with no data.
            if not data_header['channels']:
                while receiver.has_more():
                    raw_data = receiver.next()
                return_value['header'] = header
                return_value['pulse_id_array'] = pulse_id_array

                return_value['data'] = 'No channel'
                return_value['timestamp'] = None
                return_value['timestamp_offset'] = None
                return_value['pulse_ids'] = None

                return return_value

            self.receive_functions = get_receive_functions(data_header)

            return_value['data_header'] = data_header
        else:
            # Skip second header
            receiver.next()

        # Receiving data
        counter = 0
        msg_data_size = 0
        while receiver.has_more():
            raw_data = receiver.next()
            msg_data_size += len(raw_data)

            if raw_data:
                endianness = self.receive_functions[counter][0]["encoding"]
                data.append(self.receive_functions[counter][1].get_value(raw_data, endianness=endianness))

                if receiver.has_more():
                    raw_timestamp = receiver.next()
                    timestamp_array = numpy.fromstring(raw_timestamp, dtype=endianness+'u8')
                    # secPastEpoch = value[0]
                    # nsec = value[1]
                    timestamp.append(timestamp_array[0])
                    timestamp_offset.append(timestamp_array[1])
                    pulse_ids.append(pulse_id)
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
