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
    Display and/or return information about the DS9 windows currently registered
    with XPA.

    Parameters
    ----------
    verbose : bool
        If True, prints out all the information about what ds9s are active.

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
    nameserver is running at all.
    """
    session_list = []

    # only run if XPA/xpans is installed on the machine
    if find_xpans():
        try:
            sessions = xpa.get(b"xpans")
            if sessions is None and verbose:
                print("No active sessions")
            if len(sessions) < 1 and verbose:
                print("No active sessions")
            else:
                for line in sessions.decode().split('\n'):
                    if line.strip() != '':
                        session_list.append(sessions.decode().split())
                if verbose:
                    print(sessions.decode())
        except xpa.XpaException:
            if verbose:
                print("No active sessions registered")

    elif verbose:
        print("XPA nameserver not installed or not on PATH, \
               function unavailable")

    return session_list


def display_help():
    """Display RTD html help in a browser window"""
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
        logging.basicConfig(
            filename=filename,
            level=level,
            format='\n%(funcName)s \n%(message)s',
        )
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('\n%(funcName)s \n%(message)s')
        stdout_handler.setFormatter(formatter)

        root.addHandler(stdout_handler)
        # to prevent warning in unhandled contexts
        root.addHandler(logging.NullHandler())

        print("Saving imexam commands to {0:s}".format(filename))
        return root

    if not on:
        logging.disable(logging.CRITICAL)  # basically turns off logging


def check_filetype(filename=None):
    """check the file to see if it is a multi-extension fits file
    or a simple fits image where the data and header are together
    """
    if not filename:
        raise ValueError("No filename provided")
    else:
        try:
            mef_file = fits.getval(filename, ext=0, keyword='EXTEND')
        except KeyError:
            mef_file = False

        # check to see if the fits file lies
        if mef_file:
            try:
                nextend = fits.getval(filename, ext=0, keyword='NEXTEND')
            except KeyError:
                mef_file = False

        return mef_file


def verify_filename(fname="", extver=None, extname=None, getshort=False):
    """
    Verify the filename exists and check to see if the
    user has given extension, extension name or some combination
    """

    if fname:
        # see if the image is MEF or Simple
        fname = os.path.abspath(fname)
        try:
            # strip the extensions for now
            shortname = fname.split("[")[0]
            if getshort:
                return shortname

            mef_file = check_filetype(shortname)
            if not mef_file or '[' in fname:
                chunk = fname.split(",")
                cstring = ('file fits {0:s} {1:d}'.format(shortname, extver))
            elif extver and not extname:
                cstring = ('file fits {0:s} {1:d}'.format(fname, extver))
            elif extver and extname:
                cstring = (
                    'file fits {0:s} {1:s} {2:d}'.format(
                        fname,
                        extname,
                        extver))
        except IOError as e:
            print("Exception: {0}".format(e))
            raise IOError

        return cstring
    else:
        print("No filename provided")
