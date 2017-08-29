import math


def waveform(pulse_id):
    waveform = []
    for index in range(0, 30, 1):
        grad = (3.1415 * index / float(200)) + pulse_id / float(100)
        waveform.append(math.sin(grad))
    return waveform


def image(pulse_id):
    image = []
    for i in range(2):
        image.append([1.0, 2.0, 3.0, 4.0])
    return image


simulated_channels = [{"name": 'ABC', "function": lambda x: x, "metadata": {'type': 'int32'}},
                      {"name": 'ABCD', "function": lambda x: x * 10.0},
                      {"name": 'ABCDF', "function": lambda x: x * 100.0},
                      {"name": 'XYZ', "function": lambda x: x * 200.0},
                      {"name": 'XYZW', "function": lambda x: 'hello', "metadata": {'type': 'string'}},
                      {"name": 'WWW', "function": lambda x: [1.0, 2.0, 3.0, 4.0], "metadata":
                          {'type': 'float64', 'shape': [4]}
                       },
                      {"name": 'WAVE', "function": waveform, "metadata": {'shape': [30]}},
                      {"name": 'IMAGE', "function": image, "metadata": {'shape': [2, 4]}}]


def generate_stream(port, n_messages=None, interval=0.01):
    from .sender import Sender

    generator = Sender(port=port)

    for channel in simulated_channels:
        generator.add_channel(**channel)

    generator.generate_stream(n_messages=n_messages, interval=interval)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='bsread simulation utility')
    parser.add_argument('-p', '--port', type=int, default='9999', help='Port number of stream')
    parser.add_argument('-n', '--n_messages', type=int, default=None, help="Number of messages to generate."
                                                                           "None means infinity.")
    parser.add_argument('-i', '--interval', type=float, default=0.01, help="Interval in seconds between messages."
                                                                         "Default: 0.01 second.")

    arguments = parser.parse_args()

    generate_stream(port=arguments.port, n_messages=arguments.n_messages, interval=arguments.interval)


if __name__ == "__main__":
    main()
