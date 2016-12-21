
def usage():

    print('')
    print('Usage: bs [OPTIONS] COMMAND [arg...]')
    print('')
    print('Commands:')
    print('')
    print(' config          - Configure IOC')
    print(' stats           - Show receiving statistics')
    print(' receive         - Basic receiver')
    print(' h5              - Dump stream into HDF5 file')
    print(' create          - Create a test softioc')
    print(' simulate        - Provide a test stream')
    print(' avail           - Show currently available beam synchronous channels')
    print('')
    print('Run \'bs COMMAND --help\' for more information on a command.')
    print('')


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
        except ImportError:            
            print(command + ' - Command not found')
            usage()
            exit(-1)

    command_script.main()


if __name__ == "__main__":

    main()
