from . import create_test_db


def create_test_ioc_config(ioc_prefix, port, dbs_to_load=None):
    startup_script = """require "bsread"
runScript $(bsread_DIR)/bsread_sim.cmd, "SYS={prefix},BSREAD_PORT={port}"
    """.format(port=port, prefix=ioc_prefix.upper())

    # print startup_script

    if dbs_to_load:
        startup_script = startup_script + '\ndbLoadRecords("{filename}","P={prefix}-FAKEDATA")\n'.format(filename=dbs_to_load, prefix=ioc_prefix.upper())

    with open("startup.cmd", 'w') as f:
        f.write(startup_script)

    # Print environment variables to be set to access this ioc
    import socket

    print()
    print('# To start the test ioc use ')
    print('iocsh startup.cmd')
    print()
    print('# Afterwards the ioc date stream is accessible via tcp://'+socket.gethostname()+':%d' % int(port))
    print('# The ioc configuration port is accessible via tcp://' + socket.gethostname() + ':%d' % (int(port)+1))
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='bsread create utility - creates a sample ioc configuration')

    parser.add_argument('prefix', type=str, help='ioc prefix')
    parser.add_argument('port', type=int, help='ioc stream port')
    parser.add_argument('--db', type=str, help="""

    create additional test database with specified number of scalars and waveforms
    using generator strings (e.g. 'scalar(10);waveform(10,1024)')

    input commands must be delimited with ';'.

    Available input commands:
        scalar([no of scalars])
        waveform([no of waveforms],[size of waveform])

    """)

    arguments = parser.parse_args()

    if arguments.db:
        create_test_db.create_db(arguments.db, "test.template")
        create_test_ioc_config(arguments.prefix, arguments.port, "test.template")
    else:
        create_test_db.create_db("scalar(40); waveform(10,124)", "test.template")
        create_test_ioc_config(arguments.prefix, arguments.port)

if __name__ == "__main__":
    main()
