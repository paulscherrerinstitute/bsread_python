#!/usr/bin/env python

import mflow
from .handlers.extended import Handler
import zmq
from . import writer as wr
import logging

# Logger configuration
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(name)s - %(message)s')


def receive(source, file_name):
    receiver = mflow.connect(source, conn_type="connect", mode=zmq.PULL)
    handler = Handler()

    writer = wr.Writer()
    writer.open_file(file_name)

    first_iteration = True

    try:
        while True:
            message_data = receiver.receive(handler=handler.receive)
            message_data = message_data.data

            if message_data['header']['hash'] == '':
                print('SKIPPING FIRST MESSAGE !!!!')
                continue

            if first_iteration and "data_header" in message_data:
                data_header = message_data['data_header']
                print("Data Header: ", data_header)
                first_iteration = False

                writer.add_dataset('/pulse_id', dataset_group_name='pulse_id_array', dtype='i8')

                # Interpret the data header and add required datasets
                for channel in data_header['channels']:
                    dtype = 'f8'

                    if 'type' not in channel:  # Default
                        dtype = 'f8'
                    elif channel['type'].lower() == 'double':
                        dtype = 'f8'
                    elif channel['type'].lower() == 'float':
                        dtype = 'f4'
                    elif channel['type'].lower() == 'integer':
                        dtype = 'i4'
                    elif channel['type'].lower() == 'long':
                        dtype = 'i4'
                    elif channel['type'].lower() == 'ulong':
                        dtype = 'u4'
                    elif channel['type'].lower() == 'short':
                        dtype = 'i2'
                    elif channel['type'].lower() == 'ushort':
                        dtype = 'u2'

                    # elif channel['type'].lower() == 'int8':
                    #     dtype = 'i1'
                    # elif channel['type'].lower() == 'uint8':
                    #     dtype = 'u1'
                    elif channel['type'].lower() == 'int16':
                        dtype = 'i2'
                    elif channel['type'].lower() == 'uint16':
                        dtype = 'u2'
                    elif channel['type'].lower() == 'int32':
                        dtype = 'i4'
                    elif channel['type'].lower() == 'uint32':
                        dtype = 'u4'
                    elif channel['type'].lower() == 'int64':
                        dtype = 'i8'
                    elif channel['type'].lower() == 'uint64':
                        dtype = 'u8'
                    elif channel['type'].lower() == 'float32':
                        dtype = 'f4'
                    elif channel['type'].lower() == 'float64':
                        dtype = 'f8'

                    else:
                        # we are skipping strings as they are not supported ...
                        # string, int8, uint8 ...
                        writer.add_dataset_stub(dataset_group_name='data')
                        writer.add_dataset_stub(dataset_group_name='timestamp')
                        writer.add_dataset_stub(dataset_group_name='timestamp_offset')
                        writer.add_dataset_stub(dataset_group_name='pulse_ids')
                        continue

                    if 'shape' in channel:
                        shape = [1] + channel['shape']
                        maxshape = [None] + channel['shape']
                        print(shape, "  ", maxshape, channel['name'])
                        writer.add_dataset('/'+channel['name']+'/data', dataset_group_name='data', shape=shape,
                                           maxshape=maxshape, dtype=dtype)
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


def main():
    from .cli_utils import EnvDefault
    import argparse
    parser = argparse.ArgumentParser(description='BSREAD hdf5 utility')

    parser.add_argument('-s', '--source', action=EnvDefault, envvar='BS_SOURCE', type=str, help='Source address - format "tcp://<address>:<port>"')
    parser.add_argument('file', type=str, help='Destination file')

    arguments = parser.parse_args()

    address = arguments.source

    import re
    if not re.match('^tcp://', address):
        print('Protocol not defined for address - Using tcp://')
        address = 'tcp://' + address
    if not re.match('.*:[0-9]+$', address):
        print('Port not defined for address - Using 9999')
        address += ':9999'
    if not re.match('^tcp://[a-zA-Z.\-0-9]+:[0-9]+$', address):
        print('Invalid URI - ' + address)
        exit(-1)

    try:
        receive(address, arguments.file)

    except(TypeError, AttributeError):
        # Usually AttributeError is thrown if the receiving is terminated via ctrl+c
        # As we don't want to see a stacktrace then catch this exception
        pass


if __name__ == "__main__":
    main()
