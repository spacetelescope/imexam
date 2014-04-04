# Licensed under a 3-clause BSD style license - see LICENSE.rst

from .util import *
import connect as _connect
connect=_connect.Connect

try:
    import astropy
    from astropy.io import fits as pyfits
except ImportError:
    print("astropy not loaded")
    try:    
        import pyfits
    except ImportError:
        print("pyfits is not installed, please install for full functionality")

