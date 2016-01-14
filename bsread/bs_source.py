from . import create_test_db


def create_test_ioc_config(ioc_prefix, port, dbs_to_load=None):
    startup_script = """require "bsread"
runScript $(bsread_DIR)/bsread_sim.cmd, "SYS={prefix},BSREAD_PORT={port}"
    """.format(port=port, prefix=ioc_prefix.upper())

    # print startup_script

    if(dbs_to_load):
        startup_script = startup_script + '\ndbLoadRecords("{filename}","P={prefix}-FAKEDATA")\n'.format(filename=dbs_to_load,prefix=ioc_prefix.upper())

    with open("startup.cmd", 'w') as f:
        f.write(startup_script)

    # Print environment variables to be set to access this ioc
    import socket
    print_set_environment(socket.gethostname(), port)

    print('')
    print('# To start the test ioc use ')
    print('iocsh startup.cmd')
    print('')


def print_set_environment(ioc, port):
    print('')
    print('# To set the environment automatically use:')
    print('# eval "$(bs-source env '+ioc+' %d)"' % int(port))
    print('')
    print('export BS_SOURCE=tcp://'+ioc+':%d' % int(port))
    print('export BS_CONFIG=tcp://'+ioc+':%d' % (int(port)+1))
    print('')


def print_unset_environment():
    print('')
    print('# To unset the environment use:')
    print('# eval "$(bs-source clear_env)"')

    print('unset BS_SOURCE')
    print('unset BS_CONFIG')
    print('')


def main():
    import argparse

    parser = argparse.ArgumentParser(description='bsread source utility')

    subparsers = parser.add_subparsers(title='subcommands', description='Subcommands', help='additional help',
                                       dest='subparser')
    parser_create = subparsers.add_parser('create', help="Create configuration files for a test ioc")
    parser_create.add_argument('prefix', type=str, help='ioc prefix')
    parser_create.add_argument('port', type=int, help='ioc stream port')
    parser_create.add_argument('--db', type=str, help="""

    create additional test database with specified number of scalars and waveforms
    using generator strings (e.g. 'scalar(10);waveform(10,1024)')

    input commands must be delimited with ';'.

    Available input commands:
        scalar([no of scalars])
        waveform([no of waveforms],[size of waveform])

    """)

    parser_env = subparsers.add_parser('env', help='Display environment variable for easy use of bs command')
    parser_env.add_argument('ioc', type=str, help='ioc name')
    parser_env.add_argument('port', type=str, default='9999', nargs='?', help='port number of stream')

    subparsers.add_parser('clear_env', help='Display how to clear environmentvariables')

    arguments = parser.parse_args()

    if arguments.subparser == 'env':
        print_set_environment(arguments.ioc, arguments.port)
        exit(0)

    if arguments.subparser == 'create':
        if(arguments.db):
            create_test_db.create_db(arguments.db,"test.template")
            create_test_ioc_config(arguments.prefix, arguments.port,"test.template")
        else:
            create_test_db.create_db("scalar(40); waveform(10,124)","test.template")
            create_test_ioc_config(arguments.prefix, arguments.port)

    if arguments.subparser == 'clear_env':
        print_unset_environment()
        exit(0)


if __name__ == "__main__":
    main()
