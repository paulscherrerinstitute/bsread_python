#!/usr/bin/env python

import bsread
import zmq
import writer as wr


if __name__ == "__main__":
    receiver = bsread.Bsread(mode=zmq.PULL)
    receiver.connect(address="tcp://localhost:9999", conn_type="connect", )

    writer = wr.Writer()
    writer.open_file('test.h5')

    try:
        while True:
            message_data = receiver.receive()
            if "data_header" in message_data:
                data_header = message_data['data_header']
                print "Data Header: ", data_header

                # Interpret the data header and add required datasets
                for channel in data_header['channels']:
                    dtype = 'f8'
                    if channel['type'].lower() == 'integer':
                        dtype = 'i4'
                    elif channel['type'].lower() == 'long':
                        dtype = 'i8'
                    elif channel['type'].lower() == 'string':
                        # we are skipping strings as they are not supported ...
                        writer.add_dataset_stub()
                        continue

                    if 'shape' in channel:
                        shape = [1] + channel['shape']
                        maxshape = [None] + channel['shape']
                        writer.add_dataset('/'+channel['name']+'/data', shape=shape, maxshape=maxshape, dtype=dtype)
                    else:
                        writer.add_dataset('/'+channel['name']+'/data', dtype=dtype)

            data = message_data['data']
            print data
            writer.write(data)
    finally:
        writer.close_file()