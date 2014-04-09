# Licensed under a 3-clause BSD style license - see LICENSE.rst

from __future__ import print_function, division

import os
import sys
import logging
import warnings

from . import xpa
from xpa import XpaException

__all__ = ["find_ds9", "list_active_ds9", "display_help"]


def find_ds9():
    """Find the local path to the DS9 executable"""
    path = "ds9"
    for dirname in os.getenv("PATH").split(":"):
        possible = os.path.join(dirname, path)
        if os.path.isfile(possible):
            return possible


def list_active_ds9():
    """Display information about the DS9 windows currently registered with XPA and runnning


    when I start a unix socket with connect() the xpa register isn't seeing it when I call this function
    I think because it's only listening on the inet socket which starts by default. I reset the package
    to start inet connections by default, but the user can still choose unix through their env.

    """
    try:
        sessions = (xpa.get('xpans'))
        if len(sessions) < 1:
            print("No active sessions")
        else:
            print(sessions)
    except XpaException as e:
        print("No active sessions")


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
DEFAULT_LOGFILE = "imexam_session.log"


def set_logging(on=True, filename=None, level=logging.DEBUG):
    """Turn on or off logging to a file

    basicConfig defaults to opening the file in append mode
    There's still an issue here that if the user deletes the
    log file and then continues on with functions which log
    information, no new file is opened again and nothing gets written
    """
    if on:
        if not filename:
            filename = DEFAULT_LOGFILE

        root = logging.getLogger(__name__)
        logging.basicConfig(filename=filename, level=level, format='\n%(funcName)s \n%(message)s',)
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('\n%(funcName)s \n%(message)s')
        stdout_handler.setFormatter(formatter)

        root.addHandler(stdout_handler)
        root.addHandler(logging.NullHandler())  # to prevent warning in unhandled contexts

        print("Saving imexam commands to {0:s}".format(filename))
        return root

    if not on:
        logging.disable(logging.CRITICAL)
