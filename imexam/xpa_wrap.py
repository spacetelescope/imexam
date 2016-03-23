# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function, division, absolute_import

from imexam.xpa import xpa
import sys

class XPA(xpa):

    def __init__(self, template):
        xpa.__init__(self,template.encode('utf-8'))

    # for all interaction with xpa user functions
    def get(self, param=None):
        if int(sys.version[0]) < 3:
            r=xpa.get(self, param.encode('utf-8'))
            return r.decode()
        else:
            return xpa.get(self,param.encode('utf-8')).decode()

    def set(self, param=None, buf=None):
        xpa.set(self,param.encode(), buf)

    # return a list of access point id's
    def nslookup(self):
        return xpa.nslookup()
