
def main():
    import argparse
    parser = argparse.ArgumentParser(description='BSREAD utility')

    subparsers = parser.add_subparsers(title='subcommands', description='Subcommands', help='additional help',
                                       dest='subparser')
    parser_create = subparsers.add_parser('create')
    parser_env = subparsers.add_parser('env')
    parser_env.add_argument('ioc', type=str, help='ioc name')
    parser_env.add_argument('port', type=str, default='9999', nargs='?', help='port number of stream')

    arguments = parser.parse_args()

    if arguments.subparser == 'env':
        print '#Use eval "$(bs-machine env '+arguments.ioc+' '+arguments.port+')"'
        print '#To set the environment automatically'
        print ''
        print 'export BS_SOURCE=tcp://'+arguments.ioc+':%d' % int(arguments.port)
        print 'export BS_CONFIG=tcp://'+arguments.ioc+':%d' % (int(arguments.port)+1)
        exit(0)

    if arguments.subparser == 'create':
        pass


if __name__ == "__main__":
    main()
