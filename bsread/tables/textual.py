from rich.console import Console
from textual.app import App
from textual.widgets import DataTable as TableWidget

from .bases import BaseDataTable


class TextualTable(BaseDataTable):

    def __init__(self, receive_func, channel_filter):
        self.console = Console()
        max_rows = max(1, self.console.size.height - 1)
        super().__init__(receive_func, channel_filter, max_rows)
        self.app = TableApp(self.data)

    def run(self):
        self.app.run()


class TableApp(App):

    BINDINGS = [("ctrl+c", "quit")]
    CSS = "DataTable { height: 100%; width: 100%; }"

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.table = TableWidget()

    def compose(self):
        yield self.table

    def on_mount(self):
        self.set_interval(0.1, self.make_table)

    def make_table(self):
        data = self.data
        table = self.table
        table.clear(columns=True)
        table.add_columns(*data.cols)
        for row in data.rows:
            table.add_row(*row)



