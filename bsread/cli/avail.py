import click
from bsread import dispatcher
from bsread.cli import utils
import re


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("pattern", default=".*")
@click.option("--all", "metadata", default=False, is_flag=True, help="Display meta information")
@click.option("--base_url", default=None, help="URL of dispatcher")
@click.option("--backend", default=None, help="Backend to query")
def avail(pattern=None, base_url=None, backend=None, metadata=False):

    base_url = utils.get_base_url(base_url, backend)

    pattern = ".*" + pattern + ".*"

    try:
        channels = dispatcher.get_current_channels(base_url=base_url)
        for channel in channels:
            if re.match(pattern, channel["name"]):
                if metadata:
                    click.echo(f"{channel['name']:50} {channel['type']} {channel['shape']} "
                               f"{channel['modulo']} {channel['offset']} {channel['source']}")
                else:
                    click.echo(channel["name"])
    except Exception as e:
        click.echo(f"Unable to retrieve channels\nReason:\n{e}", err=True)


def main():
    avail()


if __name__ == "__main__":
    avail()
