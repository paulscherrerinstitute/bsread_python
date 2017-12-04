#!/usr/bin/env python

import mflow
from bsread.data.serialization import channel_type_deserializer_mapping
from bsread.handlers import extended
import zmq
from . import writer as wr
from . import dispatcher
import logging

# Logger configuration
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(name)s - %(message)s')


def receive(source, file_name, queue_size=100, mode=zmq.PULL, n_messages=None, message_processor=None):
    handler = extended.Handler()
    receiver = mflow.connect(source, conn_type="connect", queue_size=queue_size, mode=mode)

    if message_processor is None:
        message_processor = process_message

    writer = wr.Writer()
    writer.open_file(file_name)

    first_iteration = True

    if not n_messages:
        n_messages = -1

    try:
        while n_messages != 0:
            success = message_processor(handler, receiver, writer, first_iteration)

            if success:
                first_iteration = False
                n_messages -= 1

    finally:
        writer.close_file()


def process_message_compact(handler, receiver, writer, first_iteration):
    message_data = receiver.receive(handler=handler.receive)

    # In case you set a receive timeout, the returned message can be None.
    if message_data is None:
        return False

    message_data = message_data.data

    if message_data['header']['hash'] == '':
        print('SKIPPING FIRST MESSAGE !!!!')
        return False

    if first_iteration and "data_header" in message_data:
        data_header = message_data['data_header']
        print("Data Header: ", data_header)

        writer.add_dataset('/pulse_id', dataset_group_name='pulse_id_array', dtype='i8')

        # Interpret the data header and add required datasets
        for channel in data_header['channels']:
            channel_type = channel.get('type')

            # TODO: Add string support.
            if channel_type and channel_type.lower() == "string":
                # we are skipping strings as they are not supported ...
                writer.add_dataset_stub(dataset_group_name='data')
                continue

            dtype = channel_type_deserializer_mapping[channel_type][0]

            if 'shape' in channel:
                # H5 is slowest dimension first, but bsread is fastest dimension first.
                shape = [1] + channel['shape'][::-1]
                maxshape = [None] + channel['shape'][::-1]

                print(shape, "  ", maxshape, channel['name'])
                writer.add_dataset('/data/' + channel['name'], dataset_group_name='data', shape=shape,
                                   maxshape=maxshape, dtype=dtype)
            else:
                writer.add_dataset('/data/' + channel['name'], dataset_group_name='data', dtype=dtype)

    data = message_data['data']
    logger.debug(data)

    writer.write(data, dataset_group_name='data')
    writer.write(message_data['pulse_id_array'], dataset_group_name='pulse_id_array')


    return True


def process_message(handler, receiver, writer, first_iteration):

    message_data = receiver.receive(handler=handler.receive)

    # In case you set a receive timeout, the returned message can be None.
    if message_data is None:
        return False

    message_data = message_data.data

    if message_data['header']['hash'] == '':
        print('SKIPPING FIRST MESSAGE !!!!')
        return False

    if first_iteration and "data_header" in message_data:
        data_header = message_data['data_header']
        print("Data Header: ", data_header)

        writer.add_dataset('/pulse_id', dataset_group_name='pulse_id_array', dtype='i8')

        # Interpret the data header and add required datasets
        for channel in data_header['channels']:
            channel_type = channel.get('type')

            # TODO: Add string support.
            if channel_type and channel_type.lower() == "string":
                # we are skipping strings as they are not supported ...
                writer.add_dataset_stub(dataset_group_name='data')
                continue

            dtype = channel_type_deserializer_mapping[channel_type][0]

            if 'shape' in channel:
                # H5 is slowest dimension first, but bsread is fastest dimension first.
                shape = [1] + channel['shape'][::-1]
                maxshape = [None] + channel['shape'][::-1]

                print(shape, "  ", maxshape, channel['name'])
                writer.add_dataset('/' + channel['name'] + '/data', dataset_group_name='data', shape=shape,
                                   maxshape=maxshape, dtype=dtype)
            else:
                writer.add_dataset('/' + channel['name'] + '/data', dataset_group_name='data', dtype=dtype)

            # Add new datasets (in different dataset groups) for timestamp, timestamp_offset and pulse_ids
            writer.add_dataset('/' + channel['name'] + '/timestamp', dataset_group_name='timestamp', dtype='i8')
            writer.add_dataset('/' + channel['name'] + '/timestamp_offset', dataset_group_name='timestamp_offset',
                               dtype='i8')
            writer.add_dataset('/' + channel['name'] + '/pulse_id', dataset_group_name='pulse_ids', dtype='i8')

    data = message_data['data']
    logger.debug(data)

    writer.write(data, dataset_group_name='data')
    writer.write(message_data['pulse_id_array'], dataset_group_name='pulse_id_array')

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description='BSREAD hdf5 utility')

    parser.add_argument('-s', '--source', type=str, default=None,
                        help='Source address - format "tcp://<address>:<port>"')
    parser.add_argument('file', type=str, help='Destination file')
    parser.add_argument('channel', type=str, nargs='*',
                        help='Channels to retrieve (from dispatching layer)')
    parser.add_argument('-m', '--mode', default='pull', choices=['pull', 'sub'], type=str,
                        help='Communication mode - either pull or sub (default depends on the use of -s option)')
    parser.add_argument('-q', '--queue', default=100, type=int,
                        help='Queue size of incoming queue (default = 100)')
    parser.add_argument('-n', '--n_messages', type=int, default=None, help="Number of messages to receive."
                                                                           "None means infinity.")
    parser.add_argument("--compact", dest="compact_format", action="store_true", help="Use the compact version of the "
                                                                                      "file format.")

    arguments = parser.parse_args()

    filename = arguments.file
    address = arguments.source
    channels = arguments.channel
    queue_size = arguments.queue

    mode = mflow.SUB if arguments.mode == 'sub' else mflow.PULL
    use_dispatching = False

    if not channels and not address:
        print('\nNo source nor channels are specified - exiting!\n')
        parser.print_help()
        exit(-1)

    if address:
        import re
        if not re.match('^tcp://', address):
            # print('Protocol not defined for address - Using tcp://')
            address = 'tcp://' + address
        if not re.match('.*:[0-9]+$', address):
            # print('Port not defined for address - Using 9999')
            address += ':9999'
        if not re.match('^tcp://[a-zA-Z.\-0-9]+:[0-9]+$', address):
            print('Invalid URI - ' + address)
            exit(-1)
    else:
        # Connect via the dispatching layer
        use_dispatching = True
        address = dispatcher.request_stream(channels)
        mode = zmq.SUB

    # Use the compact H5 format if so specified.
    if arguments.compact_format:
        message_processor = process_message_compact
    else:
        message_processor = None

    try:
        receive(address, filename, queue_size=queue_size, mode=mode, n_messages=arguments.n_messages,
                message_processor=message_processor)

    except KeyboardInterrupt:
        # KeyboardInterrupt is thrown if the receiving is terminated via ctrl+c
        # As we don't want to see a stacktrace then catch this exception
        pass
    finally:
        if use_dispatching:
            print('Closing stream')
            dispatcher.remove_stream(address)


if __name__ == "__main__":
    main()
