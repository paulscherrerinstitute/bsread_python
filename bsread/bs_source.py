
def create_test_ioc_config(ioc_prefix, port):

    startup_script = """require "bsread"
runScript $(bsread_DIR)/bsread_sim.cmd, "SYS={prefix},BSREAD_PORT={port}"
dbLoadRecords("bsread_test.template","P={prefix}-FAKEDATA")
    """.format(port=port, prefix=ioc_prefix.upper())
    # print startup_script

    with open("startup.cmd", 'w') as f:
        f.write(startup_script)

    # Get test template from Git server
    # https://github.psi.ch/projects/ST/repos/bsread/browse/example/bsread_test.template?&raw
    import urllib2
    response = urllib2.urlopen('https://github.psi.ch/projects/ST/repos/bsread/browse/example/bsread_test.template?&raw')
    template = response.read()
    # print template

    with open("bsread_test.template", 'w') as f:
        f.write(template)

    print 'To start the test ioc use '
    print 'iocsh startup.cmd'

    # Print environment variables to be set to access this ioc
    import socket
    print_set_environment(socket.gethostname(), port)




def print_set_environment(ioc, port):
    print ''
    print '# To set the environment automatically use:'
    print '# eval "$(bs-source env '+ioc+' %d)"' % int(port)
    print ''
    print 'export BS_SOURCE=tcp://'+ioc+':%d' % int(port)
    print 'export BS_CONFIG=tcp://'+ioc+':%d' % (int(port)+1)
    print ''


def print_unset_environment():
    print ''
    print '# To unset the environment use:'
    print '# eval "$(bs-machine clear_env)"'

    print 'unset BS_SOURCE'
    print 'unset BS_CONFIG'
    print ''


def main():
    import argparse

    parser = argparse.ArgumentParser(description='BSREAD utility')

    subparsers = parser.add_subparsers(title='subcommands', description='Subcommands', help='additional help',
                                       dest='subparser')
    parser_create = subparsers.add_parser('create')
    parser_create.add_argument('prefix', type=str, help='ioc prefix')
    parser_create.add_argument('port', type=int, help='ioc stream port')

    parser_env = subparsers.add_parser('env')
    parser_env.add_argument('ioc', type=str, help='ioc name')
    parser_env.add_argument('port', type=str, default='9999', nargs='?', help='port number of stream')

    subparsers.add_parser('clear_env')

    arguments = parser.parse_args()

    if arguments.subparser == 'env':
        print_set_environment(arguments.ioc, arguments.port)
        exit(0)

    if arguments.subparser == 'create':
        create_test_ioc_config(arguments.prefix, arguments.port)

    if arguments.subparser == 'clear_env':
        print_unset_environment()
        exit(0)


if __name__ == "__main__":
    main()
