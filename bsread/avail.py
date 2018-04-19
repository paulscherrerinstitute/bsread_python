from . import dispatcher
import re
import sys


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Get available beam synchronous channels')

    parser.add_argument('pattern', type=str, nargs='?', help='Regex channel pattern')
    parser.add_argument('-a', '--all', action='store_true', default=False, help='Display all meta information')

    arguments = parser.parse_args()

    pattern = arguments.pattern
    print_metadata = arguments.all

    if not pattern:
        pattern = '.*'

    pattern = '.*' + pattern + '.*'

    try:
        channels = dispatcher.get_current_channels()
        for channel in channels:
            if re.match(pattern, channel['name']):
                if print_metadata:
                    print("{:50} {} {} {} {} {}".format(channel['name'], channel['type'], channel['shape'],
                                                        channel['modulo'], channel['offset'], channel['source']))
                    # print(channel)
                else:
                    print(channel['name'])
    except Exception as e:
        print('Unable to retrieve channels\nReason:\n' + str(e), file=sys.stderr)


if __name__ == "__main__":
    main()
