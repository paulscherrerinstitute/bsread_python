
def usage():

    print ''
    print 'Usage: bs [OPTIONS] COMMAND [arg...]'
    print ''
    print 'Commands:'
    print ''
    print ' config          - Configure IOC'
    print ' stats           - Show receiving statistics'
    print ' receive         - Basic receiver'
    print ' h5              - Dump stream into HDF5 file'
    print ' ioc             - Display environment variables for given ioc'
    print '                   eval(bs ioc <iocname>)'
    print ''
    print 'Run \'bs COMMAND --help\' for more information on a command.'
    print ''


def main():

    import sys

    # Remove the first two arguments (i.e. script name and command)
    sys.argv.pop(0)

    # If no sub-command is specified - print usage
    if len(sys.argv) < 1:
        usage()
        exit(0)

    command = sys.argv[0]

    import importlib
    try:
        command_script = importlib.import_module(command)
    except:
        try:
            command_script = importlib.import_module('bsread.'+command)
        except:
            print command + ' - Command not found'
            usage()
            exit(-1)

    # Check whether there are BS environment variables set
    # Some hacking because not all command can be handled the same way - i.e. config, h5
    import os
    environment_var_config = 'BS_CONFIG'
    environment_var_source = 'BS_SOURCE'
    if command == 'config':
        if environment_var_config in os.environ:
            print 'Using config ' + os.environ[environment_var_config]
            sys.argv.append(os.environ[environment_var_config])
    else:
        if command == 'h5' and environment_var_source in os.environ:
            sys.argv.insert(-1, os.environ[environment_var_source])
        elif environment_var_source in os.environ:
            print 'Using source ' + os.environ[environment_var_source]
            sys.argv.append(os.environ[environment_var_source])

    command_script.main()


if __name__ == "__main__":

    main()
