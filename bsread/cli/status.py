import click

from bsread import dispatcher
from .utils import get_base_url


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("channel", nargs=-1)
@click.option("--base_url", default=None, help="URL of dispatcher")
@click.option("--backend", default=None, help="Backend to query")
def status(channel, base_url=None, backend=None):
    base_url = get_base_url(base_url, backend)

    try:
        data = dispatcher.get_channel_status(channel, base_url=base_url)
        table(data)
    except Exception as e:
        click.echo(f"Unable to retrieve channel status\nReason:\n{e}", err=True)


def table(d):
    cols = ["configured", "connected", "recording", "last event"]
    headers = ["name"] + cols

    rows = [
        [name] + [attrs.get(c, "") for c in cols] for name, attrs in d.items()
    ]

    table = [headers] + rows
    widths = [max(len(str(v)) for v in col) for col in zip(*table)]

    underlines = ["-" * w for w in widths]
    table.insert(1, underlines)

    for row in table:
        print("   ".join(str(v).ljust(widths[i]) for i, v in enumerate(row)))


def main():
    status()





if __name__ == "__main__":
    main()



