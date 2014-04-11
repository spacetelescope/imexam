# Licensed under a 3-clause BSD style license - see LICENSE.rst

from imexam.xpa import xpa

class XPA(xpa):

    def __init__(self, template):
        xpa.__init__(self, template.encode("ascii"))

    # for all interaction with xpa user functions
    def get(self, param=""):
        r = xpa.get(self, param.encode("ascii"))
        return r.decode()

    def set(self, param="", buf=None):
        xpa.set(self, param.encode("ascii"), buf)

    #return a list of access point id's
    def nslookup(self):
       return xpa.nslookup()
