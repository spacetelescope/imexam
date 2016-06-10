# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
A package to help perform image examination through a viewing tool, like DS9
This is an Astropy affiliated package
"""

# import high level functions into the imexam namespace
from .util import find_ds9
from .util import list_active_ds9
from .util import display_help
from .util import find_xpans
from .util import set_logging
from . import connect as _connect
connect = _connect.Connect

try:
    import astropy
except ImportError:
    raise ImportError("astropy required but not found")

try:
    from .version import version as __version__
except ImportError:
    __version__ = ''
try:
    from .version import githash as __githash__
except ImportError:
    __githash__ = ''
