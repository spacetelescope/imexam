"""Licensed under a 3-clause BSD style license - see LICENSE.rst."""

from __future__ import print_function, division, absolute_import
from xpa import xpa


class XPA(xpa):
    """Interface with the xpa for ds9"""

    def __init__(self, template="imexam"):
        super(XPA, self).__init__(template.encode('utf-8', 'strict'))

    def get(self, param=""):
        """Get information from the xpa."""
        return super(XPA, self).get(param.encode('utf-8', 'strict')).decode()

    def set(self, param="", buf=None):
        """send information to the xpa."""
        super(XPA, self).set(param.encode('utf-8', 'strict'), buf)
