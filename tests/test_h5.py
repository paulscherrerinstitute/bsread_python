import unittest
from threading import Thread

import h5py
import os
from bsread import simulate, h5
from bsread.h5 import process_message_compact
from bsread.simulate import simulated_channels


class TestWriter(unittest.TestCase):

    h5_test_filename = "temp_h5.h5"

    def tearDown(self):
        if os.path.exists(self.h5_test_filename):
            os.remove(self.h5_test_filename)

    def test_receive(self):

        n_messages = 5
        generate_thread = Thread(target=simulate.generate_stream, args=(9999, n_messages,))
        generate_thread.daemon = True
        generate_thread.start()

        source = "tcp://localhost:9999"

        h5.receive(source, self.h5_test_filename, n_messages=n_messages)

        generate_thread.join()

        file = h5py.File(self.h5_test_filename)

        expected_channels = set((x["name"] for x in simulated_channels))
        # Pulse id is added to the h5 file.
        expected_channels.add("pulse_id")

        self.assertSetEqual(set(file.keys()), expected_channels)

        # Pulse_id is a dataset, inspect it separately.
        expected_channels.remove("pulse_id")

        for channel_name in expected_channels:
            self.assertSetEqual(set(file[channel_name].keys()),
                                {"data", "timestamp", "timestamp_offset", "pulse_id"})

            self.assertEqual(len(file[channel_name]["data"]), n_messages)
            self.assertEqual(len(file[channel_name]["timestamp"]), n_messages)
            self.assertEqual(len(file[channel_name]["timestamp_offset"]), n_messages)
            self.assertEqual(len(file[channel_name]["pulse_id"]), n_messages)

        self.assertEqual(len(file["pulse_id"]), n_messages)

    def test_receive_none(self):

        n_messages = 20
        generate_thread = Thread(target=generate_real_stream, args=(9999, n_messages,))
        generate_thread.daemon = True
        generate_thread.start()

        source = "tcp://localhost:9999"

        h5.receive(source, self.h5_test_filename, n_messages=n_messages)

        generate_thread.join()

        file = h5py.File(self.h5_test_filename)

        expected_channels = set((x["name"] for x in simulated_channels))
        # Pulse id is added to the h5 file.
        expected_channels.add("pulse_id")

        self.assertSetEqual(set(file.keys()), expected_channels)

        # Pulse_id is a dataset, inspect it separately.
        expected_channels.remove("pulse_id")

        for channel_name in expected_channels:
            self.assertSetEqual(set(file[channel_name].keys()),
                                {"data", "timestamp", "timestamp_offset", "pulse_id"})

            self.assertEqual(len(file[channel_name]["data"]), n_messages)

        self.assertEqual(len(file["pulse_id"]), n_messages)

    def test_compact_processor(self):
        n_messages = 5
        generate_thread = Thread(target=simulate.generate_stream, args=(9999, n_messages,))
        generate_thread.daemon = True
        generate_thread.start()

        source = "tcp://localhost:9999"

        h5.receive(source, self.h5_test_filename, n_messages=n_messages, message_processor=process_message_compact)

        generate_thread.join()

        file = h5py.File(self.h5_test_filename)

        expected_channels = set((x["name"] for x in simulated_channels))

        self.assertSetEqual(set(file["data"].keys()), expected_channels)

        for channel_name in expected_channels:
            self.assertTrue(channel_name in file["data"])
            self.assertEqual(len(file["data"][channel_name]), n_messages)

        self.assertTrue("pulse_id" in file.keys())
        self.assertEqual(len(file["pulse_id"]), n_messages)


def generate_real_stream(port, n_messages=None, interval=0.01):
    from bsread.sender import Sender

    generator = Sender(port=port)

    for channel in simulated_channels:
        generator.add_channel(**channel)

    generator.generate_stream(n_messages=n_messages, interval=interval)

