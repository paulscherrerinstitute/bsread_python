import os
import glob

__all__ = []
htypes = {}
for f in glob.glob(os.path.dirname(__file__) + "/*.py"):
    if os.path.isfile(f) and not os.path.basename(f).startswith('_'):
        __all__.append(os.path.basename(f)[:-3])

def load(htype):
    import importlib
    # Todo: Add some more logic to use an more general handler if possible
    # i.e. htype-1.2 can be handled with an htype_1.py handler
    s_type = importlib.import_module("."+htype.replace('.', '_').replace('-', '_'), __name__)
    # s_type = __import__("handler." + htype.replace('.', '_').replace('-', '_'), fromlist=".")
    return s_type.Handler()
