from time import sleep

from rich.console import Console
from rich.table import Table
from rich.live import Live

from .bases import BaseDataTable


class RichTable(BaseDataTable):

    def __init__(self, receive_func, channel_filter, _clear):
        self.console = Console()
        max_rows = max(1, self.console.size.height - 4) #if clear else None
        super().__init__(receive_func, channel_filter, max_rows)

    def run(self):
        with Live(console=self.console, auto_refresh=False) as live:
            while True:
                live.update(self.make_table(), refresh=True)
                sleep(0.1)

    def make_table(self):
        tab = Table(show_lines=False)
        for col in self.data.cols:
            tab.add_column(col)
        for row in self.data.rows:
            tab.add_row(*row)
        return tab



