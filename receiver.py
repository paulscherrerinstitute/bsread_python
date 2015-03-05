#!/usr/bin/env python

import bsread
import zmq
import writer as wr
import logging

# Logger configuration
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(name)s - %(message)s')


def receive(source, file_name):
    receiver = bsread.Bsread(mode=zmq.PULL)
    receiver.connect(address=source, conn_type="connect", )

    writer = wr.Writer()
    writer.open_file(file_name)

    try:
        while True:
            message_data = receiver.receive()
            if "data_header" in message_data:
                data_header = message_data['data_header']
                print "Data Header: ", data_header

                # Define endianness of data
                # > - big endian
                # < - little endian
                endianness = '<' # default little endian
                if 'encoding' in data_header and data_header['encoding'] == 'big':
                    endianness = '>'
                print "Using endianness: "+endianness

                writer.add_dataset('/pulse_id', dataset_group_name='pulse_id_array', dtype='i8')

                # Interpret the data header and add required datasets
                for channel in data_header['channels']:
                    dtype = endianness+'f8'
                    if channel['type'].lower() == 'integer':
                        dtype = endianness+'i4'
                    elif channel['type'].lower() == 'long':
                        dtype = endianness+'i8'
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
            logger.debug(data)

            writer.write(message_data['pulse_id_array'], dataset_group_name='pulse_id_array')

            writer.write(data, dataset_group_name='data')
            writer.write(message_data['timestamp'], dataset_group_name='timestamp')
            writer.write(message_data['timestamp_offset'], dataset_group_name='timestamp_offset')
            writer.write(message_data['pulse_ids'], dataset_group_name='pulse_ids')

    finally:
        writer.close_file()


if __name__ == "__main__":
    import sys
    import getopt

    source_ = 'tcp://localhost:9999'  # 'tcp://gfa-lc6-64:9999'
    file_name_ = 'test.h5'

    arguments = sys.argv[1:]
    usage = sys.argv[0]+' -s <source> -f <output_file>'

    try:
        opts, args = getopt.getopt(arguments, "hs:f:", ["source=", "file="])
    except getopt.GetoptError:
        print usage
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print usage
            sys.exit()
        elif opt in ("-s", "--source"):
            source_ = arg
        elif opt in ("-f", "--file"):
            file_name_ = arg

    receive(source_, file_name_)