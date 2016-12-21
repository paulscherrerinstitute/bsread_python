def generate_stream(port):
    from .sender import Sender
    import math

    def waveform(pulse_id):
        waveform = []
        for index in range(0, 30, 1):
            grad = (3.1415*index/float(200))+pulse_id/float(100)
            waveform.append(math.sin(grad))
        return waveform

    def image(pulse_id):
        image = []
        for i in range(2):
            # line = []
            # for index in range(0, 30, 1):
            #     grad = (3.1415*index/float(200))+pulse_id/float(100)
            #     line.append(math.sin(grad))
            # image.append(line)
            image.append([1.0, 2.0, 3.0, 4.0])
        return image

    generator = Sender(port=port)
    generator.add_channel('ABC', lambda x: x, metadata={'type': 'int32'})
    generator.add_channel('ABCD', lambda x: x*10.0)
    generator.add_channel('ABCDF', lambda x: x*100.0)
    generator.add_channel('XYZ', lambda x: x*200.0)
    generator.add_channel('XYZW', lambda x: 'hello', metadata={'type': 'string'})
    generator.add_channel('WWW', lambda x: [1.0, 2.0, 3.0, 4.0], metadata={'type': 'float64', 'shape': [4]})
    generator.add_channel('WAVE', waveform, metadata={'shape': [30]})
    generator.add_channel('IMAGE', image, metadata={'shape': [2, 4]})
    generator.generate_stream()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='bsread simulation utility')
    parser.add_argument('-p', '--port', type=str, default='9999', help='Port number of stream')

    arguments = parser.parse_args()

    generate_stream(int(arguments.port))

if __name__ == "__main__":
    main()
