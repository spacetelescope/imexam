"""Licensed under a 3-clause BSD style license - see LICENSE.rst."""

import os
import sys
import logging
import warnings
from astropy.io import fits

from . import __version__

try:
    from . import imexamxpa as xpa
    _have_xpa = True
except ImportError:
    _have_xpa = False


# To guide any import *
__all__ = ["display_help", "set_logging"]


def find_path(target=None):
    """Find the local path to the target executable.

    Parameters
    ----------
    target: None or str
        The name of the executable to find

    Returns
    -------
    The path to the executable or None if not found

    Notes
    -----
    This will first look for the target on the users
    path and then look to see if an alias has been
    set. It assumes that the user has aliased ds9 to
    the same name, ds9. If otherwise, the user should
    specify path in the call to the connect() method.
    """

    if target is None:
        raise TypeError("Expected name of target executable")

    found_path = None
    for dirname in os.getenv("PATH").split(":"):
        possible = os.path.join(dirname, target)
        if os.path.isfile(possible):
            found_path = possible
    if found_path is None:
        # This will also return None if not set
        found_path = os.getenv(target)
    return found_path


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
    nameserver is running at all.
    """
    session_dict = {}

    # only run if XPA/xpans is installed on the machine
    if find_path('xpans'):
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
        except (ValueError, xpa.XpaException):
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
            url += f"en/v{__version__}/"
        webbrowser.open(url)
    except ImportError:
        warnings.warn(
            f"webbrowser module not installed, see {url} for help")
        raise ImportError


def display_xpa_help():
    """Display help for XPA Acccess Points."""
    url = "http://ds9.si.edu/doc/ref/xpa.html"
    try:
        import webbrowser
        webbrowser.open(url)
    except ImportError:
        warnings.warn(
            f"webbrowser module not installed, see {url} for help")
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
            print(f"Saving imexam commands to {repr(filename)}")
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


def check_valid(fits_data=None):
    """Check the file to see if it is a multi-extension FITS file
    or a simple fits image where the data and header are stored in
    the primary header unit.

    Parameters
    ----------
    fits_data: None, FITS object
        Set to an in-memory FITS object if passing FITS HDUList;
        Otherwise set to the name of the file to check

    Returns
    -------
    mef_file: bool
        Returns True if the file is a multi-extension fits file
    nextend: int
        The number of extension in the file
    first_image: int, None
        The extension that contains the first image data.
        None will be returned when no IMAGE xtension is found

    Notes
    -----
    Drizzled images put a table in the first extension and an image in
    the zero extension, so this function checks for the first occurrance
    of 'IMAGE' in 'XTENSION', which is a required keyword.
    """
    log = logging.getLogger(__name__)
    found_image = False  # Does it contain an IMAGE XTENSION
    nextend = 0  # how many extenions does it have
    first_image = None  # what extension has the first image?
    fits_file = False
    mef_file = False

    if fits_data is None:
        raise ValueError("No filename or FITS object provided")
    if isinstance(fits_data, fits.hdu.hdulist.HDUList):
        mef_file = True
        fits_image = fits_data
    elif isinstance(fits_data, fits.hdu.image.PrimaryHDU):
        if fits_data.header['NAXIS'] > 0:
            first_image = 0
        fits_image = fits_data
    elif isinstance(fits_data, str):
        fits_file = True
        try:
            fits_image = fits.open(fits_data)
        except IOError:
            msg = f"Error opening file {repr(fits_data)}"
            log.warning(msg)
            raise IOError(msg)
        try:
            # EXTEND is required for MEF FITS files
            mef_file = fits_image[0].header['EXTEND']
            if not mef_file:
                if fits_image[0].header['NAXIS'] > 0:
                    first_image = 0
        except KeyError:
            if fits_image[0].header['NAXIS'] > 0:
                first_image = 0

    #  double check for lying liars, should at least have 1 extension
    #  if it's MEF and XTENSION is a required keyword in each extension
    #  after the primary hdu
    if mef_file:
        for extn in fits_image:
            try:
                if ((extn.header['XTENSION'] == 'IMAGE') and (not found_image)):
                    first_image = nextend  # The number of the extension
                    found_image = True
            except KeyError:
                # There doens't have to be an 'XTENSION' keyword in the global(0) if
                # the MEF has data there, so check for naxis if its an image
                # and tfields if it's table data
                if nextend == 0:
                    try:
                        tfields = extn.header['TFIELDS']  # table?
                    except KeyError:
                        if extn.header['NAXIS'] > 0:
                            found_image = True
                            first_image = nextend
                else:
                    mef_file = False
            nextend += 1
        nextend -= 1  # account for overcounting in return value
    if fits_file:
        fits_image.close()
    return (mef_file, nextend, first_image)


def verify_filename(filename=None, extver=None, extname=None):
    """Verify the filename exists and split it for extension information.
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

    Returns
    -------
    shortname: str
        The name of the file with full path
    extname: str, None
        The extension name, or None
    extver: int, None
        The extension version number or None
    """
    if filename is None:
        print("No filename provided")
    elif not isinstance(filename, str):
        raise TypeError("Expected filename to be a string")
    else:
        if "[" in filename:
            splitstr = filename.split("[")
            shortname = os.path.abspath(splitstr[0])
            if "," in splitstr[1]:
                extname = splitstr[1].split(",")[0]
                extver = int(splitstr[1].split(",")[1][0])
            else:
                extver = int(filename.split("[")[1][0])
        else:
            shortname = os.path.abspath(filename)
    return shortname, extname, extver
