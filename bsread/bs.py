USAGE = """
Usage: bs [OPTIONS] COMMAND [arg...]

Commands:
 config          - Configure IOC
 stats           - Show receiving statistics
 receive         - Basic receiver
 h5              - Dump stream into HDF5 file
 create          - Create a test softioc
 simulate        - Provide a test stream
 avail           - Show currently available beam synchronous channels

Run \'bs COMMAND --help\' for more information on a command.
"""


def usage():
    print(USAGE.strip())


def main():
    import sys

    # Remove the first arguments (i.e. the script name)
    sys.argv.pop(0)

    # If no sub-command is specified - print usage
    if len(sys.argv) < 1:
        usage()
        exit(0)

    command = sys.argv[0]
    if command.startswith("-"):
        usage()
        exit(0)

    import importlib

    try:
        command_script = importlib.import_module('bsread.' + command)
    except ImportError as e:
        # this catches not only the ImportError from importing the command here
        # but also ImportErrors inside the command
        print(command + ' - Command not found (' + str(e) + ')')
        usage()
        exit(-1)

    command_script.main()


if __name__ == "__main__":
    main()
