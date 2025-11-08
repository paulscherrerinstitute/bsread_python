from rich.console import Console
from textual.app import App
from textual.widgets import DataTable as TableWidget

from .bases import BaseDataTable


class TextualTable(BaseDataTable):

    def __init__(self, receive_func, channel_filter, _clear):
        self.console = Console()
        max_rows = max(1, self.console.size.height - 1) #if clear else None
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

        data_rows = data.rows
        data_cols = data.cols

        table_cols = get_cols(table)

        # only rebuild columns if they changed
        if table_cols != data_cols:
            table.clear(columns=True)
            table.add_columns(*data_cols)

        n_data_rows = len(data_rows)
        n_table_rows = len(table.rows)

        # update the existing rows
        for i, row in enumerate(data_rows[:n_table_rows]):
            update_row_at(table, i, row)

        # add missing rows
        for row in data_rows[n_table_rows:]:
            table.add_row(*row)

        # remove extra rows
        for row_index in reversed(range(n_data_rows, n_table_rows)):
            remove_row_at(table, row_index)



def get_cols(table):
    # ck => textual.widgets._data_table.ColumnKey
    # ck.label => rich.text.Text
    return [ck.label.plain for ck in table.columns.values()]

def update_row_at(table, row_index, values, update_width=False):
    for col_index, val in enumerate(values):
        coord = (row_index, col_index)
        table.update_cell_at(coord, val, update_width=update_width)

def remove_row_at(table, row_index):
    col_index = 0
    coord = (row_index, col_index)
    row_key, _col_key = table.coordinate_to_cell_key(coord)
    table.remove_row(row_key)



