# Licensed under a 3-clause BSD style license - see LICENSE.rst

from .util import *
import connect as _connect
connect = _connect.Connect

try:
    import astropy
except ImportError:
    raise ImportError("astropy required but not found")
    
from astropy.io import fits 
