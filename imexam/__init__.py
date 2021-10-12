# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
An Astropy affiliated  package to help perform image examination through a
viewing tool, like DS9
"""

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *  # noqa
# ----------------------------------------------------------------------------

try:
    from . import imexamxpa  # noqa
    _have_xpa = True
except ImportError:
    _have_xpa = False

# import high level functions into the imexam namespace
if _have_xpa:
    from .util import list_active_ds9, find_path  # noqa
    from .util import display_help, display_xpa_help  # noqa

from .util import set_logging  # noqa
from . import connect as _connect
connect = _connect.Connect
