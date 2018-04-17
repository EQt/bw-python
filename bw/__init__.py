from .bw import BigWig, open

__version__ = "0.0.2"

def doctests():
    from . import bw
    import doctest
    doctest.testmode(m=bw)
