import unittest
from threading import Thread

import h5py
import numpy
import os

from mflow import mflow, zmq

from bsread import writer, simulate, h5
from bsread.data.helpers import get_channel_specs
from bsread.h5 import receive
from bsread.handlers import extended
from bsread.sender import sender
from bsread.simulate import simulated_channels


class TestWriter(unittest.TestCase):

    h5_test_filename = "temp_h5.h5"

    def tearDown(self):
        if os.path.exists(self.h5_test_filename):
            os.remove(self.h5_test_filename)

    def test_receive(self):

        n_messages = 5
        generate_thread = Thread(target=simulate.generate_stream, args=(9999, n_messages,))
        generate_thread.setDaemon(True)
        generate_thread.start()

        source = "tcp://localhost:9999"

        h5.receive(source, self.h5_test_filename, n_messages=n_messages)

        generate_thread.join()

        file = h5py.File(self.h5_test_filename)

        expected_channels = set((x["name"] for x in simulated_channels))
        # Strings are not supported in h5 file.
        expected_channels.remove("XYZW")
        # Pulse id is added to the h5 file.
        expected_channels.add("pulse_id")

        self.assertSetEqual(set(file.keys()), expected_channels)

        # Pulse_id is a dataset, inspect it separately.
        expected_channels.remove("pulse_id")

        for channel_name in expected_channels:
            self.assertSetEqual(set(file[channel_name].keys()),
                                set(("data", "timestamp", "timestamp_offset", "pulse_id")))

            self.assertEqual(len(file[channel_name]["data"]), n_messages)

        self.assertEqual(len(file["pulse_id"]), n_messages)

    def test_receive_none(self):

        n_messages = 20
        generate_thread = Thread(target=generate_real_stream, args=(9999, n_messages,))
        generate_thread.setDaemon(True)
        generate_thread.start()

        source = "tcp://localhost:9999"

        h5.receive(source, self.h5_test_filename, n_messages=n_messages)

        generate_thread.join()

        file = h5py.File(self.h5_test_filename)

        expected_channels = set((x["name"] for x in simulated_channels))
        # Strings are not supported in h5 file.
        # Pulse id is added to the h5 file.
        expected_channels.add("pulse_id")

        self.assertSetEqual(set(file.keys()), expected_channels)

        # Pulse_id is a dataset, inspect it separately.
        expected_channels.remove("pulse_id")

        for channel_name in expected_channels:
            self.assertSetEqual(set(file[channel_name].keys()),
                                set(("data", "timestamp", "timestamp_offset", "pulse_id")))

            self.assertEqual(len(file[channel_name]["data"]), n_messages)

        self.assertEqual(len(file["pulse_id"]), n_messages)


simulated_channels = [{"name": 'ABC', "function": lambda x: x, "metadata": {'type': 'int32'}},
                      {"name": 'ABCD', "function": lambda x: x * 10.0},
                      {"name": 'ABCDF', "function": lambda x: None if x % 10 else x * 100.0},  # GENERATE NULL values
                      {"name": 'XYZ', "function": lambda x: x * 200.0},
                      {"name": 'WWW', "function": lambda x: [1.0, 2.0, 3.0, 4.0], "metadata":
                          {'type': 'float64', 'shape': [4]}
                       }]


def generate_real_stream(port, n_messages=None, interval=0.01):
    from bsread.sender import Sender

    generator = Sender(port=port)

    for channel in simulated_channels:
        generator.add_channel(**channel)

    generator.generate_stream(n_messages=n_messages, interval=interval)

