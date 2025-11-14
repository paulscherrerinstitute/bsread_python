import importlib
import sys


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

Run 'bs COMMAND --help' for more information on a command.
"""


def quit(error=None):
    if error:
        print(error)
        print()
    print(USAGE.strip())
    raise SystemExit(True if error else False)


def main():
    # Remove the first arguments (i.e. the script name)
    sys.argv.pop(0)

    # If no sub-command is specified, quit
    if len(sys.argv) < 1:
        quit()

    # If any switch is given or this command itself, quit
    command = sys.argv[0]
    if command.startswith("-") or command == "bs":
        quit()

    try:
        command_script = importlib.import_module("bsread.cli." + command)
    except ImportError as e:
        # this catches not only the ImportError from importing the command here
        # but also ImportErrors inside the command
        en = type(e).__name__
        quit(f"{command} - Command not found ({en}: {e})")

    command_script.main()


if __name__ == "__main__":
    main()


