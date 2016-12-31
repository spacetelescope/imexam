"""Licensed under a 3-clause BSD style license - see LICENSE.rst."""

from __future__ import print_function, division

import os
import sys
import logging
import warnings
from astropy.io import fits

import xpa
from .version import version as __version__

# To guide any import *
__all__ = [
    "find_ds9",
    "list_active_ds9",
    "display_help",
    "find_xpans",
    "set_logging"]


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


def list_active_ds9(verbose=True):
    """
    Display and/or return information about the DS9 windows currently
    registered with the XPA.

    Parameters
    ----------
    verbose : bool
        If True, prints out all the information about what DS9 windows
        are active.

    Returns
    -------
    session_list : list
        The list of sessions that have been registered.  Each entry in the list
        is a list containing the information that xpans yields.  Typically the
        fourth element in that tuple contains the actual target name.

    Notes
    -----
    when I start a unix socket with connect() the xpa register isn't
    seeing it when I call this function. I think because it's only
    listening on the inet socket which starts by default in the OS.
    That's if xpans is installed on the machine. Otherwise, no
    nameserver is running at all. This helps with object cont
    """
    session_dict = {}

    # only run if XPA/xpans is installed on the machine
    if find_xpans():
        sessions = None
        try:
            sessions = xpa.get(b"xpans").decode().strip().split("\n")
            if ((sessions is None or len(sessions) < 1) and verbose):
                print("No active sessions")
            else:
                for line in sessions:
                    classn, name, access, ids, user = tuple(line.split())
                    session_dict[ids] = (name, user, classn, access)
                if verbose:
                    for line in sessions:
                        print(line)
        except xpa.XpaException:
                print("No active sessions registered")

    else:
        print("XPA nameserver not installed or not on PATH, \
               function unavailable")

    return session_dict


def display_help():
    """Display RTD html help for the installed verison in a browser window."""
    url = "http://imexam.readthedocs.io/"
    try:
        import webbrowser
        # grab the version that's installed
        if "dev" not in __version__:
            url += "en/{0:s}/".format(__version__)
        webbrowser.open(url)
    except ImportError:
        warnings.warn(
            "webbrowser module not installed, see {0:s} for help".format(url))
        raise ImportError


def display_xpa_help():
    """Display help for XPA Acccess Points."""
    url = "http://ds9.si.edu/doc/ref/xpa.html"
    try:
        import webbrowser
        webbrowser.open(url)
    except ImportError:
        warnings.warn(
            "webbrowser module not installed, see {0:s} for help".format(url))
        raise ImportError


# Set up logging ability for the user
# consider making a private logging level for data retension
def set_logging(filename=None, on=True, level=logging.INFO):
    """Turn on or off logging to file or stdout.

    Parameters
    ----------

    filename: str, optional
        name of the file for logging information
    on: bool, optional
        turn logging on or off, will close the file output
        in order to turn off stdout logging, set the level
        to logging.CRITICAL
    level: logging, optional
        the logging level to be recorded or displayed

    """

    formatter = logging.Formatter('\n%(funcName)s \n%(message)s')
    root = logging.getLogger(__name__)
    root.setLevel(level)
    stream_attached = False
    file_attached = False

    if on:
        #  Try to avoid adding duplicate file handlers
        if len(root.handlers) > 0:
            for handler in root.handlers:
                if isinstance(handler, logging.StreamHandler):
                    stream_attached = True
                    handler.setLevel(level)
                if isinstance(handler, logging.FileHandler):
                    file_attached = True
                    raise ValueError("File for logging already specified,\
                                      turn off logging first.")
        else:
            # to prevent warning in unhandled contexts and messages to stderr
            root.addHandler(logging.NullHandler())

        if isinstance(filename, str) and not file_attached:
            file_handler = logging.FileHandler(filename=filename,
                                               mode='a',
                                               delay=True)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            print("Saving imexam commands to {0:s}".format(repr(filename)))
            root.addHandler(file_handler)

        if not stream_attached:
            # set the stdout stream handler
            stdout_handler = logging.StreamHandler(stream=sys.stdout)
            stdout_handler.setLevel(logging.INFO)
            # stdout_handler.setFormatter(formatter)
            root.addHandler(stdout_handler)

    #  turning the logging off to the file and set level on stream handler
    else:
        for handler in root.handlers:
            # close the file logger
            if isinstance(handler, logging.FileHandler):
                handler.close()
                root.removeHandler(handler)
            # set stream logging level
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(level)

    return root


def check_filetype(filename=None):
    """Check the file to see if it is a multi-extension FITS file
    or a simple fits image where the data and header are stored in
    the global unit.

    Parameters
    ----------
    filename: string
        The name of the file to check


    """
    log = logging.getLogger(__name__)

    if filename is None:
        raise ValueError("No filename provided")
    else:
        try:
            mef_file = fits.getval(filename, ext=0, keyword='EXTEND')
        except KeyError:
            mef_file = False
        except IOError:
            log.warning("Problem opening file {0:s}".format(repr(filename)))
            raise IOError("Error opening {0:s}".format(filename))
        return mef_file


def verify_filename(filename=None, extver=None, extname=None):
    """Verify the filename exist and split it for extension information.
    If the user has given an extension, extension name or some combination of
    those, return the full filename, extension and version tuple.

    Parameters
    ----------
    filename: string
        The name of the file to verify

    extver: int
        extsion number which corresponds to extname

    extname: string
        the name of the extension
    """
    if filename is None:
        print("No filename provided")
    else:
        try:
            if "[" in filename:
                splitstr = filename.split("[")
                shortname = splitstr[0]
                if "," in splitstr[1]:
                    extname = splitstr[1].split(",")[0]
                    extver = int(splitstr[1].split(",")[1][0])
                else:
                    extver = int(filename.split("[")[1][0])
            else:
                shortname = os.path.abspath(filename)
        except IndexError as e:
            print("Exception: {0}".format(repr(e)))
            raise IndexError

        return shortname, extname, extver
