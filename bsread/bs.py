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


def quit(error=None):
    if error:
        print(error)
        print()
    print(USAGE.strip())
    raise SystemExit(True if error else False)


def main():
    import sys

    # Remove the first arguments (i.e. the script name)
    sys.argv.pop(0)

    # If no sub-command is specified - print usage
    if len(sys.argv) < 1:
        quit()

    command = sys.argv[0]
    if command.startswith("-"):
        quit()

    import importlib

    try:
        command_script = importlib.import_module('bsread.' + command)
    except ImportError as e:
        # this catches not only the ImportError from importing the command here
        # but also ImportErrors inside the command
        quit(command + ' - Command not found (' + str(e) + ')')

    command_script.main()


if __name__ == "__main__":
    main()
