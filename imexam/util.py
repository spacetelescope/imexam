# Licensed under a 3-clause BSD style license - see LICENSE.rst

from __future__ import print_function, division

import os
import sys
import logging
import warnings

from astropy import log
from . import xpa
from xpa import XpaException

__all__ = ["find_ds9", "list_active_ds9", "display_help", "list_ds9_ids", "find_xpans"]


def find_ds9():
    """Find the local path to the DS9 executable"""
    path = "ds9"
    for dirname in os.getenv("PATH").split(":"):
        possible = os.path.join(dirname, path)
        if os.path.isfile(possible):
            return possible
    return None


def find_xpans():
    """Find the local path to the xpans executable"""
    path = "xpans"
    for dirname in os.getenv("PATH").split(":"):
        possible = os.path.join(dirname, path)
        if os.path.exists(possible):
            return possible
    return None


def list_active_ds9():
    """Display information about the DS9 windows currently registered with XPA and runnning

    Notes
    -----
    when I start a unix socket with connect() the xpa register isn't seeing it when I call this function
    I think because it's only listening on the inet socket which starts by default in the OS. That's if xpans is installed
    on the machine. Otherwise, no nameserver is running at all.
    """

    # only run if XPA/xpans is installed on the machine
    if find_xpans():
        try:
            sessions = (xpa.get('xpans'))
            if len(sessions) < 1:
                print("No active sessions")
            else:
                print(sessions)
        except XpaException:
            print("No active sessions registered")
    else:
        print("XPA nameserver not installed or not on PATH, function unavailable")


def list_ds9_ids():
    """return just the list of ds9 XPA_METHOD ids which are registered"""
    return xpa.nslookup()


def display_help():
    """ display local html help in a browser window"""
    try:
        import webbrowser
    except ImportError:
        warnings.warn(
            "webbrowser module not installed, see the installed doc directory for the HTML help pages")
        raise ImportError

    # get the user installed location of the html docs, better way?
    from . import htmlhelp
    location = (htmlhelp.__file__).split("/")
    location.pop()
    location.append("index.html")
    url = "file://" + "/".join(location)
    webbrowser.open(url)


# Set up logging ability for the user
# consider making a private logging level for data retension
def set_logging(filename=None, on=True, level=logging.DEBUG):
    """Turn on or off logging to a file

    Notes
    -----
    basicConfig defaults to opening the file in append mode
    There's still an issue here that if the user deletes the
    log file and then continues on with functions which log
    information, no new file is opened again and nothing gets written
    """
    if on:
        if not filename:
            warnings.warn("No log filename specified")
            raise ValueError
            
        root = logging.getLogger(__name__)
        logging.basicConfig(filename=filename, level=level, format='\n%(funcName)s \n%(message)s',)
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('\n%(funcName)s \n%(message)s')
        stdout_handler.setFormatter(formatter)

        root.addHandler(stdout_handler)
        root.addHandler(logging.NullHandler())  # to prevent warning in unhandled contexts

        print("Saving imexam commands to {0:s}".format(filename))
        logging.disable(level)  # log above
        return root

    if not on:
        logging.disable(logging.CRITICAL)  # basically turns off logging
