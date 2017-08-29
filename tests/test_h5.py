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


