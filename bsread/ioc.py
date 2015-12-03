
def main():
    import argparse
    parser = argparse.ArgumentParser(description='BSREAD utility')

    parser.add_argument('ioc', type=str, help='IOC to configure')
    parser.add_argument('port', type=str, help='ZMQ port data stream')

    arguments = parser.parse_args()

    if arguments.command == 'config':
        print 'export BS_SOURCE=tcp://'+arguments.ioc+':%d' % int(arguments.port)
        print 'export BS_CONFIG=tcp://'+arguments.ioc+':%d' % (int(arguments.port)+1)


if __name__ == "__main__":
    main()
