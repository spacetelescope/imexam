"""Licensed under a 3-clause BSD style license - see LICENSE.rst."""

from __future__ import print_function, division, absolute_import

from imexam.xpa import xpa
import sys



class XPA(xpa):
    """Interface with the xpa for ds9."""

    def __init__(self, template="imexam"):
        super(XPA, self).__init__(template.encode("utf-8"))
        self._template = template

    def get(self, param=""):
        """Get information from the xpa."""
        if sys.version_info.major > 2:
            r = super(XPA, self).get(param.encode("utf-8"))
            return r.decode()
        else:
            r = super(XPA, self).get(param.encode("utf-8"))
            if r is None:
                return r
            else:
                return r.decode()
        return None

    def set(self, param="", buf=None):
        """send information to the xpa."""
        if sys.version_info.major > 2:
            super(XPA, self).set(param.encode("utf-8"), buf)
        else:
            super(XPA, self).set(param, buf)
