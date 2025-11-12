
from .classic import ClassicTable
from .plain import PlainTable

try:
    from .rich import RichTable
except ImportError:
    pass

try:
    from .textual import TextualTable
except ImportError:
    pass


def available():
    suffix = "Table"
    res = {k[:-len(suffix)].lower(): v for k, v in globals().items() if k.endswith(suffix)}

    auto_order = ("textual", "rich", "plain", "classic")
    for n in auto_order:
        if n in res:
            res["auto"] = res[n]
            break

    return res

available = available()


