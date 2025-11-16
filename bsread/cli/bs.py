import importlib
import sys


COMMANDS = {
    "config":   "Configure IOC",
    "stats":    "Show receiving statistics",
    "receive":  "Basic receiver",
    "h5":       "Dump stream into HDF5 file",
    "create":   "Create a test softioc",
    "simulate": "Provide a test stream",
    "avail":    "Show currently available beam synchronous channels"
}

HEADER = "Usage: bs [OPTIONS] COMMAND [arg...]"
FOOTER = "Run 'bs COMMAND --help' for more information on a command."


def quit(error=None):
    if error:
        print(error)
        print()
    usage = make_usage(COMMANDS, HEADER, FOOTER)
    print(usage)
    raise SystemExit(True if error else False)


def make_usage(commands, header, footer):
    lines = []
    lines.append(header)
    lines.append("")
    lines.append("Commands:")
    for name, desc in commands.items():
        lines.append(f" {name:<15}- {desc}")
    lines.append("")
    lines.append(footer)
    return "\n".join(lines)


def main():
    # Remove the first arguments (i.e. the script name)
    sys.argv.pop(0)

    # If no sub-command is specified, quit
    if len(sys.argv) < 1:
        quit()

    # If command is not from allowed commands, quit
    command = sys.argv[0]
    if command not in COMMANDS:
        quit(f"{command} - Command not found")

    try:
        command_script = importlib.import_module(f"bsread.cli.{command}")
    except ImportError as e:
        # this catches not only the ImportError from importing the command here
        # but also ImportErrors inside the command
        en = type(e).__name__
        quit(f"{command} - Command not found ({en}: {e})")

    command_script.main()





if __name__ == "__main__":
    main()



