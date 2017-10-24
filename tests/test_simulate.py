import unittest
from threading import Thread

from bsread import source, simulate
from bsread.data.helpers import get_serialization_type
from bsread.handlers import extended


class TestSimulate(unittest.TestCase):
    def test_generate_stream(self):

        n_of_messages = 5
        generate_thread = Thread(target=simulate.generate_stream, args=(9999, n_of_messages,))
        generate_thread.start()

        handler = extended.Handler().receive

        with source(host="localhost") as receive_stream:
            for _ in range(n_of_messages):
                data = receive_stream.receive(handler=handler)
                received_channels = data.data["data_header"]["channels"]

                self.assertEqual(len(received_channels), len(simulate.simulated_channels),
                                 "Not all simulated channels were received.")

                for index, received_channel in enumerate(received_channels):
                    value = data.data["data"][index]

                    receive_name = received_channel["name"]
                    receive_type = received_channel.get("type")
                    receive_shape = received_channel.get("shape")

                    send_name = simulate.simulated_channels[index]["name"]
                    send_type = simulate.simulated_channels[index].get("metadata", {}).get("type", None)
                    send_shape = simulate.simulated_channels[index].get("metadata", {}).get("shape", None)

                    self.assertEqual(receive_name, send_name, "Channels are not in same order.")
                    self.assertEqual(receive_type, send_type)
                    self.assertEqual(receive_shape, send_shape)

                    # Check if the generated type is the same as the received one.
                    value_sample = simulate.simulated_channels[index]["function"](0)

                    if isinstance(value_sample, (int, float)):
                        # Scalars have an empty shape.
                        self.assertListEqual(list(value.shape), [])

                    elif isinstance(value_sample, str):
                        self.assertTrue(isinstance(value, str))

                    if not isinstance(value, str):
                        if send_type:
                            self.assertEqual(value.dtype, get_serialization_type(send_type))

                        if send_shape:
                            # Numpy is slowest dimension first, but bsread is fastest dimension first.
                            self.assertListEqual(list(value.shape), send_shape[::-1])

        generate_thread.join()
