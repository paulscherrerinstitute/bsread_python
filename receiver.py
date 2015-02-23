#!/usr/bin/env python

import bsread
import zmq
import writer as wr


if __name__ == "__main__":
    receiver = bsread.Bsread(mode=zmq.PULL)
    receiver.connect(address="tcp://localhost:9999", conn_type="connect", )
    # receiver.connect(address="tcp://gfa-lc6-64:9999", conn_type="connect", )

    writer = wr.Writer()
    writer.open_file('test.h5')

    try:
        while True:
            message_data = receiver.receive()
            if "data_header" in message_data:
                data_header = message_data['data_header']
                print "Data Header: ", data_header

                writer.add_dataset('/pulse_id', dataset_group_name='pulse_id_array', dtype='i8')

                # Interpret the data header and add required datasets
                for channel in data_header['channels']:
                    dtype = 'f8'
                    if channel['type'].lower() == 'integer':
                        dtype = 'i4'
                    elif channel['type'].lower() == 'long':
                        dtype = 'i8'
                    elif channel['type'].lower() == 'string':
                        # we are skipping strings as they are not supported ...
                        writer.add_dataset_stub(dataset_group_name='data')
                        writer.add_dataset_stub(dataset_group_name='timestamp')
                        writer.add_dataset_stub(dataset_group_name='timestamp_offset')
                        writer.add_dataset_stub(dataset_group_name='pulse_ids')
                        continue

                    if 'shape' in channel:
                        shape = [1] + channel['shape']
                        maxshape = [None] + channel['shape']
                        writer.add_dataset('/'+channel['name']+'/data', dataset_group_name='data', shape=shape, maxshape=maxshape, dtype=dtype)
                    else:
                        writer.add_dataset('/'+channel['name']+'/data', dataset_group_name='data', dtype=dtype)

                    # Add new datasets (in different dataset groups) for timestamp, timestamp_offset and pulse_ids
                    writer.add_dataset('/'+channel['name']+'/timestamp', dataset_group_name='timestamp', dtype='i8')
                    writer.add_dataset('/'+channel['name']+'/timestamp_offset', dataset_group_name='timestamp_offset', dtype='i8')
                    writer.add_dataset('/'+channel['name']+'/pulse_id', dataset_group_name='pulse_ids', dtype='i8')

            data = message_data['data']
            print data

            writer.write(message_data['pulse_id_array'], dataset_group_name='pulse_id_array')

            writer.write(data, dataset_group_name='data')
            writer.write(message_data['timestamp'], dataset_group_name='timestamp')
            writer.write(message_data['timestamp_offset'], dataset_group_name='timestamp_offset')
            writer.write(message_data['pulse_ids'], dataset_group_name='pulse_ids')

    finally:
        writer.close_file()