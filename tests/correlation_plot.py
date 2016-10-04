from bsread import source
from bsread import PULL
from bsread import SUB

import collections
import signal


receive_more = True


def main():
    global receive_more
    receive_more = True

    def stop(*arguments):
        global receive_more
        receive_more = False
        # signal.siginterrupt()

    signal.signal(signal.SIGINT, stop)

    queue_x = collections.deque(maxlen=10)
    queue_y = collections.deque(maxlen=10)

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()

    plt.ion()
    plt.show()

    with source(channels=[{'name': 'Float64Scalar', 'modulo': 10}], mode=SUB,
                dispatcher_url='http://localhost:8080') as stream:

        while receive_more:
            message = stream.receive()
            print(message.data.data['Float64Scalar'].value)
            queue_x.append(message.data.data['Float64Scalar'].value)
            queue_y.append(message.data.data['Float64Scalar'].value)
            ax.clear()
            ax.scatter(queue_x, queue_y)

            plt.pause(0.0001)

    print(queue_x)
    print('done')


if __name__ == '__main__':
    main()
