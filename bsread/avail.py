from . import dispatcher
import re


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Get available beam synchronous channels')

    parser.add_argument('pattern', type=str, nargs='?', help='Regex channel pattern')

    arguments = parser.parse_args()

    pattern = arguments.pattern

    if not pattern:
        pattern = '.*'

    pattern = '.*' + pattern + '.*'

    channels = dispatcher.get_current_channels()
    for channel in channels:
        if re.match(pattern, channel['name']):
            print(channel['name'])

if __name__ == "__main__":
    main()