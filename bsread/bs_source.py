
template = """
# Macros
# P  -  Record prefix, e.g. TEST-BSREAD


record(calc, "$(P):TEST_1") {
	field(VAL,"0")
	field(INPA,"$(P):TEST_1")
	field(CALC,"A+1")
	field(SCAN,".1 second")
}

record(ai, "$(P):TEST_1-AI"){
	field(INP, "$(P):TEST_1")
	field(SCAN,".1 second")
}

record(bi, "$(P):TEST_1-BI"){
	field(INP, "$(P):TEST_1")
	field(SCAN,".1 second")
}

record(longin, "$(P):TEST_1-LI"){
	field(INP, "$(P):TEST_1")
	field(SCAN,".1 second")
}

record(calc, "$(P):TEST_2") {
	field(VAL,"0")
	field(INPA,"$(P):TEST_2")
	field(CALC,"A+0.1")
	field(SCAN,".1 second")
}
record(calc, "$(P):TEST_3") {
	field(VAL,"0")
	field(INPA,"$(P):TEST_3")
	field(CALC,"A+0.01")
	field(SCAN,".1 second")
}
record(calc, "$(P):TEST_4") {
	field(VAL,"0")
	field(INPA,"$(P):TEST_4")
	field(CALC,"A+10")
	field(SCAN,".1 second")
}

record(stringin, "$(P):TEST_STRING") {
        field(VAL,"Hello world")
 }


record(waveform, "$(P):TEST_WVF-DOUBLE")
{
	field(SCAN, "Passive")
	field(NELM, "10")
	field(FTVL, "DOUBLE")
}

record(waveform, "$(P):TEST_WVF-LONG")
{
	field(SCAN, "Passive")
	field(NELM, "10")
	field(FTVL, "LONG")
}

record(waveform, "$(P):TEST_WVF-SHORT")
{
	field(SCAN, "Passive")
	field(NELM, "10")
	field(FTVL, "SHORT")
}
"""

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
    # import urllib2
    # response = urllib2.urlopen('https://github.psi.ch/projects/ST/repos/bsread/browse/example/bsread_test.template?&raw')
    # template = response.read()
    # print template

    with open("bsread_test.template", 'w') as f:
        f.write(template)

    # Print environment variables to be set to access this ioc
    import socket
    print_set_environment(socket.gethostname(), port)

    print ''
    print '# To start the test ioc use '
    print 'iocsh startup.cmd'
    print ''


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
    print '# eval "$(bs-source clear_env)"'

    print 'unset BS_SOURCE'
    print 'unset BS_CONFIG'
    print ''


def main():
    import argparse

    parser = argparse.ArgumentParser(description='bsread source utility')

    subparsers = parser.add_subparsers(title='subcommands', description='Subcommands', help='additional help',
                                       dest='subparser')
    parser_create = subparsers.add_parser('create', help="Create configuration files for a test ioc")
    parser_create.add_argument('prefix', type=str, help='ioc prefix')
    parser_create.add_argument('port', type=int, help='ioc stream port')

    parser_env = subparsers.add_parser('env', help='Display environment variable for easy use of bs command')
    parser_env.add_argument('ioc', type=str, help='ioc name')
    parser_env.add_argument('port', type=str, default='9999', nargs='?', help='port number of stream')

    subparsers.add_parser('clear_env', help='Display how to clear environmentvariables')

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
