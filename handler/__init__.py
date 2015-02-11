import os
import glob

__all__ = []
htypes = {}
for f in glob.glob(os.path.dirname(__file__) + "/*.py"):
    if os.path.isfile(f) and not os.path.basename(f).startswith('_'):
        __all__.append(os.path.basename(f)[:-3])

def load(htype):
    s_type = __import__("handler." + htype.replace('.', '_').replace('-', '_'), fromlist=".")
    return s_type.Handler()