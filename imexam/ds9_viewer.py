"""
Licensed under a 3-clause BSD style license - see LICENSE.rst

This class supports communication with DS9 through the XPA


Some code in this class was adapted from pysao, which can be found
at https://github.com/leejjoon/pysao. Specifically this package used the
existing Cython implementation to the XPA  and extended the calls to the other
available XPA executables so that more functionality is added. The API
information is available here:

http://hea-www.harvard.edu/RD/xpa/client.html#xpaopen

Using Cython will allow for broader development of the code and produce faster
runtimes for large datasets with repeated calls to the display manager.

XPA is licensed under MIT, help can be found here:
http://hea-www.cfa.harvard.edu/saord/xpa/help.html

The current XPA can be downloaded from here:
http://hea-www.harvard.edu/saord/xpa/

"""

from __future__ import print_function, division, absolute_import

import os
import shutil
import numpy as np
from subprocess import Popen
import time
import warnings
import logging
from tempfile import mkdtemp
import matplotlib.image as mpimage
import matplotlib.pyplot as plt
from matplotlib import get_backend
import atexit
from subprocess import call

# The XPA class controls interaction with DS9
from .xpa_wrap import XPA
from xpa import XpaException

from . import util
from astropy.io import fits


class UnsupportedDatatypeException(Exception):
    pass


class UnsupportedImageShapeException(Exception):
    pass

__all__ = ['ds9']


class ds9(object):
    """Control all interactions between the user and the DS9 window.

    The ds9() contructor takes a ds9 target as its main argument.
    If none is given, then a new window and process will be started.

    DS9's xpa access points are documented in the reference manual,
    but the can also be returned to the user with a call to xpaset.

    http://hea-www.harvard.edu/saord/ds9/ref/xpa.html


    Parameters
    ----------
    target: string, optional
         the ds9 target name or id (default is to start a new instance)

    path : string, optional
        path of the ds9

    wait_time : float, optional
        waiting time before error is raised

    quit_ds9_on_del : boolean, optional
        If True, try to quit ds9 when this instance is deleted.


    Attributes
    ----------

    wait_time: float
         The waiting time before error is raised

    path: string
        The path to the DS9 executable

    _xpa_name: string
        The value in XPA_METHOD, the name of the DS9 window

    _quit_ds9_on_del: boolean
         Determine whether to quit ds9 when object goes out of scope.

    _ds9_unix_name: string
        The full path filename to the unix socket, only if unix sockets are
        being used with local

    _need_to_purge: boolean
        whenever there are unix socket directories which need to be purged when
        the object goes out of scope

    _tmpd_name: string
        The full path name to the unix socket file on the local system

    _filename: string
        The name of the image that's currently loaded into DS9

    _ext: int
        Extension of the current image that is loaded. If one extension of an
        MEF file is loaded this will be 1 regardless of the extension that was
        specified (because DS9 and the XPA now see it as a single image and
        header)

    _extname: string
        If available, the EXTNAME of the MEF extension that is loaded, taken
        from the current data header

    _extver: int
        If available, the EXTVER of the MEF extension that is loaded, taken
        from the current data header

    _ds9_process: pointer
        Points to the ds9 process id on the system, returned by Popen, whenever
        this module starts DS9

    _mef_file: boolean
        The file is a multi-extension fits file

    _iscube: bookean
        The file is a multiextension fits file, and one of the extensions
        contains at least 1 additional extension (3D or more)

    _numaxis: int
        number of image planes, this is NAXIS

    _naxis: tuple
        specific image plane displayed, defaulted to 1 image plane, most
        relevant to cube fits files
    """

    # _ImgCode : copied from fits, used for displaying arrays straight to DS9
    _ImgCode = {'float32': -32,
                'float64': -64,
                'float16': -16,
                'int16': 16,
                'int32': 32,
                'int64': 64,
                'uint8': 8,
                'uint16': 16}

    _tmp_dir = ""
    _process_list = list()

    def __init__(self, target=None, path=None, wait_time=5,
                 quit_ds9_on_del=True):
        """starter.

        Notes
        -----
        I think this is a quirk in the XPA communication. The xpans, and XPA
        prefer to have all connections be of the same type. DS9 defaults to
        creating an INET connection. In some cases, if no IP address can be
        found for the computer, the startup can hang. In these cases, a local
        connection is preferred, which uses a unix filename for the socket.

        The problem arises that if the user already has DS9 windows running,
        that were started by default, the nameserver is only listening for the
        default socket type (inet) and not local. There are also cases where
        the machine running this code does not have xpa installed, so there is
        no xpans (nameserver) to run and keep track of the open connections.
        In that case, the user needs to provide this init with the name of the
        socket in their window (in XPA_METHOD) in order to create the
        connection.

        """
        # determine whether to quit ds9 also when object deleted.
        self._quit_ds9_on_del = quit_ds9_on_del
        self.wait_time = wait_time
        self._need_to_purge = False
        self._tmpd_name = None

        # dictionary where each key is a frame number, and the values are a
        # dictionary of details about the image loaded in that frame
        self._viewer = dict()
        self._current_frame = None
        self._current_slice = None

        # default starting socket type to local in order get around user xpa
        # installation issues
        self._xpa_method = "local"
        self._xpa_name = ""

        # only used for DS9 windows started from this module
        self._ds9_process = None
        self._ds9_path = None

        if path is None:
            self._ds9_path = util.find_ds9()
            if not self._ds9_path:
                raise OSError("Could not find ds9 executable on your path")

        else:
            self._ds9_path = path

        if not target:
            # Check to see if the user has chosen a preference first
            if 'XPA_METHOD' in os.environ:
                self._xpa_method = os.environ['XPA_METHOD'].lower()

            if 'inet' in self._xpa_method:
                self._xpa_name = self.run_inet_ds9()
                # xpa_name is the title of the window, the xpa can be
                # referenced with either the socket address or name
                # of the window

            elif 'local' in self._xpa_method:
                self._xpa_name, self._ds9_unix_name = self._run_unixonly_ds9()

            # tells xpa where to find sockets
            os.environ['XPA_METHOD'] = self._xpa_method

        else:
            # just register with the target the user provided
            self._xpa_name = target

        # xpa_name sets the template for the get and set commands
        self.xpa = XPA(self._xpa_name)
        if 'local' in self._xpa_method:
            self._set_frameinfo()  # initial load
        self._define_cmaps()  # dictionary of color maps

    def __str__(self):
        pass

    def __del__(self):
        """Nicely exit the DS9 process."""
        if self._quit_ds9_on_del:
            if 'local' in self._xpa_method:
                self._purge_local()
            else:
                self._stop_process()

    def _set_frameinfo(self):
        """Set the name and extension for the data displayed in current frame.

        Notes
        -----
        The absolute path reference is stored to make XPA happy in all cases,
        wherever the user started the DS9 process.

        The only consistant way to return which cube and slice that is
        displayed is with the call to "file" which has the full plane=x:y
        information, but only when looking at something other than the first
        extension for each plane. In this case, you have to look at the header
        information to see it's a cube image, and assume the first image plane
        is displayed.

        If you load a single extension from an MEF into DS9, XPA references
        the extension as 1 afterwards for access points you need to look in
        the header of the displayed image to find out what actual extension
        is loaded

        This also also gathers needed image header information
        It's possible the user has an array in the frame, for which there is no
        header or filename information

        """
        # check the current frame, if none exists, then don't continue
        frame = self.frame()
        if frame:

            if frame not in self._viewer:
                self._viewer[frame] = dict()

            try:
                user_array = self._viewer[frame]['user_array']
            except KeyError:
                user_array = None

            extver = None  # extension number
            extname = None  # name of extension
            filename = None  # filename of image
            numaxis = 2  # number of image planes, this is NAXIS
            # tuple of each image plane, defaulted to 1 image plane
            naxis = (0)
            # data has more than 2 dimensions and loads in cube/slice frame
            iscube = False
            mef_file = False  # used to check misleading headers in fits files

            load_header = False  # not used for in memory arrays
            self._current_frame = frame

            # see if any file is currently loaded into ds9,
            # xpa returns '\n' for nothing loaded
            # get the current frame
            try:
                filename_string = self.get('file').strip()
                if len(filename_string) > 1 and '\n' not in filename_string:
                    filename = str(filename_string.strip().split('[')[0])
                    self._viewer[frame]['filename'] = os.path.abspath(filename)
                    load_header = True
                else:
                    filename_string = ""

            except XpaException:
                filename_string = ""

            try:
                if "plane" in filename_string:
                    iscube = True
                    if ":" in filename_string:
                        naxis = filename_string.strip().split(']')[
                            1].split("=")[1].split(":")
                    else:
                        naxis = filename_string.strip().split(']')[
                            1].split('=')[1].split()
                    if len(naxis) == 1:
                        naxis.append("0")
                    naxis.reverse()  # for astropy.fits row-major ordering
                    naxis = map(int, naxis)
                    naxis = [
                        axis -
                        1 if axis > 0 else 0 for axis in naxis]
                    naxis = tuple(naxis)
            except ValueError:
                raise ValueError("Problem parsing filename")

            if load_header:
                # set the extension from the header information returned from
                # DS9 this is the best way to get the information if the user
                # changes the loaded file using the gui
                header_cards = fits.Header.fromstring(
                    self.get_header(),
                    sep='\n')
                mef_file = util.check_filetype(filename)
                if mef_file:
                    try:
                        extver = int(header_cards['EXTVER'])
                    except KeyError:
                        # fits doesn't require extver if there is only 1
                        # extension
                        extver = 1

                    try:
                        extname = str(header_cards['EXTNAME'])
                    except KeyError:
                        extname = None

                try:
                    numaxis = int(header_cards['NAXIS'])
                except KeyError:
                    raise KeyError("Problem getting NAXIS from header")

                if not iscube:
                    if numaxis > 2:
                        iscube = True
                        naxis = list()
                        # assume the first axis in each extension is displayed
                        for axis in range(numaxis, 2, -1):
                            naxis.append(0)
                        naxis = tuple(naxis)

            # update the viewer dictionary, if the user changes what's
            # displayed in a frame this should update correctly
            # this dictionary will be referenced in the other parts of
            # the code. This enables tracking user arrays through
            # frame changes

            self._viewer[frame] = {'filename': filename,
                                   'extver': extver,
                                   'extname': extname,
                                   'naxis': naxis,
                                   'numaxis': numaxis,
                                   'iscube': iscube,
                                   'user_array': user_array,
                                   'mef': mef_file}

        else:
            warnings.warn("No frame loaded in viewer")

    def valid_data_in_viewer(self):
        """return bool if valid file or array is loaded into the viewer."""
        frame = self.frame()

        if frame:
            self._set_frameinfo()

            if self._viewer[frame]['filename']:
                return True

            else:
                try:
                    if self._viewer[frame]['user_array'].any():
                        return True
                except AttributeError as ValueError:
                    print("error in array")
        return False

    def get_filename(self):
        """return the filename currently on display.

        This function will check if there is already a filename saved. It's
        possible that the user can connect to a ds9 window with no file loaded
        and then ask for the data file name after loading one through the ds9
        menu options. This will poll the private filename and then try and set
        one if it's empty.
        """
        # see if the user has loaded a file by hand or changed frames in the
        # gui
        frame = self.frame()
        self._set_frameinfo()
        return self._viewer[frame]['filename']

    def get_frame_info(self):
        """return more explicit information about the data displayed."""
        self._set_frameinfo()
        return self._viewer[self.frame()]

    def get_viewer_info(self):
        """Return a dictionary of information.

        The dictionary contains information about all frames which are
        loaded with data

        Notes
        -----
        Consider adding a loop to verify that all the frames still exist
        and the user has not deleted any through the gui.
        """
        self._set_frameinfo()
        return self._viewer

    @classmethod
    def _purge_tmp_dirs(cls):
        """Delete temporary directories made for the unix socket.

        When used with ipython (pylab mode), it seems that the objects
        are not properly deleted, i.e., temporary directories are not
        deleted. This is a work around for that.
        """

        if cls._tmp_dir:
            shutil.rmtree(cls._tmp_dir)

    @classmethod
    def _stop_running_process(cls):
        """stop self generated DS9 windows when user quits python window."""
        while cls._process_list:
            process = cls._process_list.pop()
            if process.poll() is None:
                process.terminate()

    def _stop_process(self):
        """stop the ds9 window process nicely.

        only if this package started it
        """
        try:
            if self._ds9_process:
                # none means not yet terminated
                if self._ds9_process.poll() is None:
                    self.set("exit")
                    if self._ds9_process in self._process_list:
                        self._process_list.remove(self._ds9_process)

        except XpaException as e:
            print("XPA Exception: {0}".format(e))

    def _purge_local(self):
        """remove temporary directories from the unix socket."""
        if not self._need_to_purge:
            return

        if not self._quit_ds9_on_del:
            warnings.warn(
                "You need to manually delete tmp. dir ({0:s})".format(
                    self._tmpd_name))
            return

        self._stop_process()
        # add a wait for the process to terminate before trying to delete the
        # tree
        time.sleep(0.5)

        try:
            shutil.rmtree(self._tmpd_name)
        except OSError:
            warnings.warn(
                "Warning : couldn't delete the temporary \
                directory ({0:s})".format(self._tmpd_name,))

        self._need_to_purge = False

    def close(self):
        """close the window and end connection."""
        # make sure we clean up the object and quit_ds9 local files
        if 'local' in self._xpa_method or 'tmp' in self._xpa_method:
            self._purge_local()
        else:
            self._stop_process()

    def run_inet_ds9(self):
        """start a new ds9 window using an inet socket connection.

        Notes
        -----
        It is given a unique title so it can be identified later.
        """
        env = os.environ

        # this is the title of the window, without a nameserver connection
        # is there a way to get the inet x:x address?
        # that should be unique enough, something better?
        xpaname = "imexam" + str(time.time())
        try:
            p = Popen([self._ds9_path,
                       "-xpa", "inet",
                       "-title", xpaname],
                      shell=False, env=env)
            self._ds9_process = p
            self._process_list.append(p)
            self._need_to_purge = False
            return xpaname

        except Exception as e:  # refine error class
            warnings.warn("Opening ds9 failed")
            print("Exception: {}".format(repr(e)))
            from signal import SIGTERM
            try:
                pidtokill = p.pid
            except NameError:
                # in case p failed at the initialization level
                pidtokill = None
            if pidtokill is not None:
                os.kill(pidtokill, SIGTERM)
            raise e

    def _run_unixonly_ds9(self):
        """start new ds9 window and connect to object using a unix socket.

        Notes
        -----
        When the xpa method in libxpa parses a given template as a unix
        socket, it checks if the template string starts with tmpdir
        (from env["XPA_TMPDIR"] or default to /tmp/.xpa). This can make
        having multiple instances of ds9 a bit difficult, but if you give it
        unique names or use the inet address you should be fine

        For unix only, we run ds9 with XPA_TMPDIR set to temporary directory
        whose prefix start with /tmp/xpa (eg, /tmp/xpa_sf23f), them set
        os.environ["XPA_TMPDIR"] (which affects xpa set and/or get command
        from python) to /tmp/xpa.
        """
        env = os.environ
        wait_time = self.wait_time

        self._tmpd_name = mkdtemp(
            prefix="xpa_" +
            env.get(
                "USER",
                ""),
            dir="/tmp")

        # this is the first directory the servers looks for on the path
        env["XPA_TMPDIR"] = self._tmpd_name

        iraf_unix = "{0:s}/.IMT".format(self._tmpd_name)
        # that should be unique enough, something better?
        title = str(time.time())
        try:
            # unix only flag disables the fifos and inet connections
            p = Popen([self._ds9_path,
                       "-xpa", "local",
                       "-unix_only", "-title", title,
                       "-unix", "{0:s}".format(iraf_unix)],
                      shell=False, env=env)

            # wait until ds9 starts and the .IMT socket exists
            while wait_time > 0:
                file_list = os.listdir(self._tmpd_name)
                if ".IMT" in file_list:
                    break
                time.sleep(0.5)
                wait_time -= 0.5

            if wait_time == 0:
                from signal import SIGTERM
                os.kill(p.pid, SIGTERM)
                print(
                    "Connection timeout with the ds9. Try to increase the \
                    *wait_time* parameter (current value \
                    is  {0:d} s)".format(self.wait_time,))

        except (OSError, ValueError, AttributeError) as e:
            warnings.warn("Starting ds9 failed")
            shutil.rmtree(self._tmpd_name)

        else:
            self._tmp_dir = self._tmpd_name
            self._ds9_process = p
            self._process_list.append(p)

        # this might be sketchy
        try:
            file_list.remove(".IMT")  # should be in the directory, if not
        except (ValueError, IOError):
            warnings.warn("IMT not found in tmp, using first thing in list")
        if len(file_list) > 0:
            xpaname = os.path.join(self._tmpd_name, file_list[0])
        else:
            shutil.rmtree(self._tmpd_name)
            raise ValueError("Problem starting ds9 local socket connection")

        env["XPA_TMPDIR"] = "/tmp/xpa"  # for all local connections
        self._need_to_purge = True
        self._xpa_method = 'local'
        return xpaname, iraf_unix

    def set_iraf_display(self):
        """Set the environemnt variable IMTDEV to the current display.

        the socket address of the current imexam.ds9 instance is used
        Notes
        -----
        For example, your pyraf commands will use this ds9 for display.

        TODO: Not sure this is still needed. Stop using IRAF.
        """
        os.environ["IMTDEV"] = "unix:{0:s}".format(self._ds9_unix_name)

    def _check_ds9_process(self):
        """Check to see if the ds9 process is still running.

        Notes
        -----
        If you start a ds9 window from the shell and then connect
        to imexam, imexam will not have a reference for the process,
        so this method ignores that state.
        """
        if self._ds9_process:
            ret = self._ds9_process.poll()
            if ret is not None:
                raise RuntimeError("The ds9 process is externally killed.")
                self._purge_local()

    def set(self, param, buf=None):
        """XPA set method to ds9 instance.

        Notes
        -----
        This function is linked with the Cython implementation

        set(param, buf=None)
        param : parameter string (eg. "fits" "regions")
        buf : aux data string (sometime string needed to be ended with CR)
        """
        self._check_ds9_process()
        self.xpa.set(param, buf)

    def get(self, param):
        """XPA get method to ds9 instance which returns received string.

        Parameters
        ----------
        param : parameter string (eg. "fits" "regions")


        Notes
        -----
        This function is linked with the Cython implementation
        get(param)

        """
        self._check_ds9_process()
        return self.xpa.get(param)

    def readcursor(self):
        """Returns the image coordinate postion and key pressed.

        Notes
        -----
        XPA returns strings of the form:  u a  257.5 239
        """
        try:
            xpa_string = self.get("imexam any coordinate image")
        except XpaException as e:
            print("Xpa problem reading cursor: {0}".format(repr(e)))
            raise KeyError
        except ValueError:
            raise ValueError("Outside of data range")

        k, x, y = xpa_string.split()

        # ds9 is returning 1 based array, set to 0-based since
        # imexamine uses numpy for array crunching
        return float(x)-1, float(y)-1, str(k)

    def alignwcs(self, on=True):
        """align wcs.

        Parameters
        ----------
        on: bool
            Align the images using the WCS in their headers
        """
        self.set("align {0:s}".format(str(on)))

    def blink(self, blink=True, interval=None):
        """Blink frames.

        Parameters
        ----------
        blink: bool, optional
            Set to True to start blinking the frames which are open

        interval: int
            Set interval equal to the length of pause for blinking


        Notes
        -----
        blink_syntax=
            Syntax:
            blink
            [true|false]
            [interval <value>]

        """
        cstring = "blink "
        if blink:
            cstring += "yes "
        else:
            cstring += "no "
            if interval:
                cstring += " {0:d}".format(interval)

        self.set(cstring)

    def clear_contour(self):
        """clear contours from the screen."""
        self.set("contour clear")

    def _define_cmaps(self):
        """setup the default color maps which are available."""
        self._cmap_syntax = """
        Syntax:
        cmap [<colormap>]
            [file]
            [load <filename>]
            [save <filename>]
            [invert true|false]
            [value <constrast> <bias>]
            [tag [load|save] <filename>]
            [tag delete]
            [match]
            [lock [true|false]]
            [open|close]

         Examples
         --------
            >obj.cmap(map="gist_heat")
            >obj.cmap(invert=True)
         """

        # is there a list I can pull automatically from ds9?
        self._cmap_colors = ["grey", "red", "green", "red", "blue", "a", "b",
                             "bb", "he", "i8", "aips0", "sls", "hsv", "heat",
                             "cool", "rainbow", "standard", "staircase",
                             "color"]

    def cmap(self, color=None, load=None, invert=False, save=False,
             filename='colormap.ds9'):
        """Set the color map table, using a defined list of options.

        Parameters
        ----------
        color: string
            color must be set to one of the available DS9 color map names

        load: string, optional
            set to the filename which is a valid colormap lookup table
            valid contrast values are from 0 to 10, and valid bias
            values are from 0 to 1

        invert: bool, optional
            invert the colormap

        save: bool, optional
            save the current colormap as a file

        filename: string, optional
            the name of the file to save the colormap to
        """
        if color:
            color = color.lower()
            if color.lower() in self._cmap_colors:
                cstring = "cmap {0:s}".format(color)
                self.set(cstring)
            else:
                print("Unrecognized color map, choose one of these:")
                print(self._cmap_colors)

        if invert:
            invert = 'yes'
            cstring = 'cmap invert {0:s}'.format(invert)
            self.set(cstring)

        if load:
            cstring = 'cmap load {0:s}'.format(load)
            self.set(cstring)

        if save:
            cstring = 'cmap save {0:s}'.format(filename)
            self.set(cstring)

        if not color and not load:
            print(self._cmap_colors)

    def colorbar(self, on=True):
        """turn the colorbar on the bottom of the window on and off.

        Parameters
        ----------
        on: bool
            Set to True to turn on the colorbar, False to turn it off

        """
        self.set("colorbar {0:s}".format(str(on)))

    def contour(self, on=True, construct=True):
        """show contours on the window.

        Parameters
        ----------
        on: bool
            Set to true to turn on contours

        construct: bool, optional
            Will open the contour dialog box which has more options

        """
        self.set("contour {0:s}".format(str(on)))
        if construct:
            self.set("contour levels")

    def contour_load(self, filename):
        """load a contour file into the window.

        Parameters
        ----------
        filename: string
            The name of the file with the contour level defined

        """
        if filename:
            self.set("contour loadlevels {0:s}".format(str(filename)))
        else:
            warnings.warn("No filename provided for contours")

    def crosshair(self, x=None, y=None, coordsys="physical",
                  skyframe="wcs", skyformat="fk5", match=False, lock=False):
        """Control the position of the crosshair in the current frame.

        crosshair mode is turned on automatically

        Parameters
        ----------

        x: string or int
            The value of x is converted to a string for the call to XPA,
            use a value here appropriate for the skyformat you choose

        y: string or int
            The value of y is converted to a string for the call to XPA,
            use a value here appropriate for the skyformat you choose

        coordsys: string, optional
            The coordinate system your x and y are defined in

        skyframe: string, optional
            If skyframe has "wcs" in it then skyformat is also sent to the XPA

        skyformat: string, optional
            Used with skyframe, specifies the format of the coordinate
            which were given in x and y

        match: bool, optional
            If set to True, then the wcs is matched for the frames

        lock: bool, optional
            If set to True, then the frame is locked in wcs
        """
        if x and y:
            if "wcs" in skyframe:
                format = skyformat
            else:
                format = ""
            self.window.set("crosshair {0:s} {1:s} {2:s} {3:s}".format(
                str(x), str(y), str(coordsys), format))
        if match:
            self.window.set("crosshair match wcs")
        if lock:
            self.window.set("crosshair lock wcs")

    def cursor(self, x=None, y=None):
        """move the cursor in the current frame to the specified image pixel.

         selected regions will also be moved

        Parameters
        ----------
        x: int
            pixel location  x coordinate to move to

        y: int
            pixel location  y coordinate to move to

        x and y are converted to strings for the call

        """
        if x and y:
            self.set("cursor {0:s} {1:s}".format(str(x), str(y)))
        else:
            warnings.warn(
                "You need to supply both an x and y location for the cursor")

    def disp_header(self):
        """Display the header of the current image to a DS9 window."""
        cstring = "header "
        try:
            self.set(cstring)  # display the header of the current frame
        except XpaException as e:
            raise XpaException("XPA Exception getting header: {0}".format(e))

    def frame(self, n=None):
        """convenience function to change or report frames.

        Parameters
        ----------
        n: int, string, optional
            The frame number to open or change to. If the number specified
            doesn't exist, a new frame will be opened
            If nothing is specified, then the current frame number will be
            returned. The value of n is converted to a string before passing
            to the XPA

        Examples
        --------
        frame(1)  sets the current frame to 1
        frame("last") set the current frame to the last frame
        frame() returns the number of the current frame
        frame("new") opens a new frame
        frame(3)  opens frame 3 if it doesn't exist already, otherwise
        goes to frame 3

        """
        frame = self.get("frame").strip()  # xpa returns '\n' for no frame

        if frame:
            if n:
                if "delete" in str(n):
                    if frame in self._viewer:
                        del self._viewer[frame]
                self.set("frame {0:s}".format(str(n)))
            else:
                try:
                    if len(frame) < 1:
                        self.set("frame 1")
                        # the user can delete frame 1, but ds9 defaults to 1,
                        # so set it
                        return '1'
                    else:
                        return str(frame)
                except XpaException as e:
                    raise XpaException(
                        "XPA Exception getting frame: {0}".format(e))
        else:
            if len(frame) < 1:
                self.set("frame 1")
                # the user can delete frame 1, but ds9 defaults to 1, so set it
                return '1'

    def iscube(self):
        """return whether a cube image is displayed in the current frame."""
        frame = self.frame()
        if frame != self._current_frame:
            self._set_frameinfo()
        else:
            return self._viewer[frame]['iscube']

    def get_slice_info(self):
        """return the slice tuple that is currently displayed."""
        self._set_frameinfo()
        frame = self.frame()

        if self._viewer[frame]['iscube']:
            image_slice = self._viewer[frame]['naxis']
        else:
            image_slice = None
        return image_slice

    def get_data(self):
        """return a numpy array of the data displayed in the current frame.

        Notes
        -----
        This is the data array that the imexam() function from connect()
        uses for analysis

        astropy.io.fits stores data in row-major format. So a 4d image would be
        [NAXIS4, NAXIS3, NAXIS2, NAXIS1]
        just the one image is retured in the case of multidimensional data, not
        the cube

        """
        # make sure the filename and extension info are correct for the current
        # frame in DS9, users can change this in the gui
        # users can change frame and slice before calling this, best to check
        self._set_frameinfo()
        frame = self.frame()
        if frame:

            if isinstance(self._viewer[frame]['user_array'], np.ndarray):
                return self._viewer[frame]['user_array']
            else:
                filename = self._viewer[frame]['filename']
                extver = self._viewer[frame]['extver']
                extname = self._viewer[frame]['extname']
                naxis = self._viewer[frame]['naxis']

                if self._viewer[frame]['mef']:
                    with fits.open(filename) as filedata:
                        if self._viewer[frame]['iscube']:
                            data = filedata[extname, extver].section[naxis]
                        else:
                            data = filedata[extname, extver].data
                    return data
                else:
                    with fits.open(filename) as filedata:
                        data = filedata[0].data
                    return data

    def get_image(self):
        """return the full image object instead of just the data array."""
        print("Returning just the data array, open the image file \
               for the full object")
        self.get_data()

    def get_header(self, fitsobj=False):
        """Return the current fits header.

        The return value is the string or None if there's a problem
        If fits is True  then a fits header object is returned instead
        """
        # TODO return the simple header for arrays which are loaded

        frame = self.frame()
        if frame != self._current_frame:
            self._set_frameinfo()

        if self._viewer[frame]['filename']:
            if fitsobj:
                header = fits.getheader(self._viewer[frame]['filename'])
            else:
                try:
                    header = self.get("fits header")
                except XpaException as e:
                    print("XPA Exception getting header: {0}".format(e))
                    return None

            return header
        else:
            warnings.warn("No file with header loaded into ds9")
            return None

    def grid(self, on=True, param=False):
        """convenience to turn the grid on and off.

        grid can be flushed with many more options

        Parameters
        ----------

        on: bool, optional
            Will turn the grid overlay on in the current frame

        param: bool, optional
            Will open the parameter dialog in DS9

        """
        self.set("grid {0:s}".format(str(on)))
        if param:
            self.set("grid open")

    def hideme(self):
        """lower the ds9 window."""
        self.set("lower")

    def embed(self):
        """Embed the viewer in a notebook."""
        print("Not Implemented for DS9")

    def load_fits(self, fname=None, extver=None, extname=None, mecube=False):
        """convenience function to load fits image to current frame.

        Parameters
        ----------
        fname: string, optional
            The name of the file to be loaded. You can specify the full
            extension in the name, such as
            filename_flt.fits[sci,1] or filename_flt.fits[1]

        extver: int, optional
            The extension to load (EXTVER in the header)

        extname: string, optional
            The name (EXTNAME in the header) of the image to load

        mecube: bool, optional
            If mecube is True, load the fits file as a cube into ds9

        Notes
        -----
        To tell ds9 to open a file whose name or path includes spaces,
        surround the path with "{...}", e.g.

        % xpaset -p ds9 file "{foo bar/my image.fits}"

        This is assuming that the image loads into the current or next
        new frame, watch the internal file and ext values because the user
        can switch frames through DS9 app itself

        XPA needs to have the absolute path to the filename so that if the
        DS9 window was started in another directory it can still find the
        file to load.
        """
        if fname is None:
            raise ValueError("No filename provided")

        frame = self.frame()  # for the viewer reference
        if frame is None:
            frame = 1  # load into first frame

        shortname, extn, extv = util.verify_filename(fname)

        # prefer name specified over key
        if extn:
            extname = extn
        if extv:
            extver = extv

        if (extv is None and extver is None):
            mef = util.check_filetype(shortname)
            if mef:
                extver = 1  # MEF fits
            else:
                extver = 0  # simple fits

        print(shortname, extname, extver)
        if mecube:
            cstring = "mecube {0:s}".format(shortname)
        else:
            if extname is None:
                cstring = ('file fits {0:s}[{1:d}]'.format(shortname, extver))
            else:
                cstring = ('file fits {0:s}[{1:s},{2:d}]'.format(
                            shortname, extname, extver))

        self.set(cstring)
        self._set_frameinfo()
        # make sure any previous reference is reset
        self._viewer[frame]['user_array'] = None

    def load_region(self, filename):
        """Load regions from a file which uses ds9 standard formatting.

        Parameters
        ----------

        filename: string
            The file containing the DS9 style region description

        """
        if os.access(filename, os.F_OK):
            self.set("regions load {0:s}".format(filename))
        else:
            warnings.warn("No such file:{0:s}".format(filename))

    def load_rgb(self, red, green, blue, scale=False, lockwcs=False):
        """load 3 images into an RGBimage frame.

        Parameters
        ----------
        red: string
            The name of the fits file loaded into the red channel

        green: string
            The name of the fits file loaded into the green channel

        blue: string
            The name of the fits file loaded into the blue channel

        scale: bool
            If True, then each image will be scaled with zscale() after loading

        lockwcs: bool
            If True, then the image positions will be locked to each other
            using the WCS information in their headers

        """
        self.set("rgb new")
        self.set("rgb channel red")
        self.load_fits(red)
        if scale:
            self.scale()
        self.set("rgb channel green")
        self.load_fits(green)
        if scale:
            self.scale()
        self.set("rgb channel blue")
        self.load_fits(blue)
        if scale:
            self.scale()
        if lockwcs:
            self.set("rgb wcs yes")

    def load_mef_as_cube(self, filename=None):
        """Load a Mult-Extension-Fits image into one frame as an image cube."""
        if not filename:
            print("No filename specified")
        else:
            self.set("file mecube new {0:s}".format(filename))

    def load_mef_as_multi(self, filename=None):
        """Load a Mult-Extension-Fits image into multiple frames."""
        if not filename:
            print("No filename specified")
        else:
            self.set("file multiframe {0:s}".format(filename))

    def mark_region_from_array(
            self, input_points, ptype="image", textoff=10, size=4):
        """mark ds9 regions regions  given an input list of tuples.

         a convienence function, you can also use set_region

        Parameters
        ----------
        input_points: iterator, a tuple, or list of tuples
                      or a string: (x,y,comment),

        ptype: string
            the reference system for the point locations, image|physical|fk5

        size: int
            the size of the region marker

        textoff: string
            the offset for the comment text, if comment is empty
            it will not show

        Notes
        -----
        only circular regions are supported currently

        """
        if isinstance(input_points, tuple):
            input_points = [input_points]
        elif isinstance(input_points, str):
            input_points = [tuple(input_points.split())]

        X = 0
        Y = 1
        COMMENT = 2
        rtype = "circle"  # only one supported right now

        for location in input_points:
            if rtype == "circle":
                pline = rtype + " " + \
                    str(location[X]) + " " + str(location[Y]) + " " + str(size)
                print(pline)
                self.set_region(pline)

            try:
                if(len(str(location[COMMENT])) > 0):
                    pline = "text " + str(float(location[X]) + textoff) + " " + \
                        str(float(location[Y]) + textoff) + " '" + \
                        str(location[COMMENT]) + "' #font=times"
                    print(pline)
                    self.set_region(pline)
            except IndexError:
                pass

    def make_region(self, infile, labels=False, header=0, textoff=10, size=5):
        """make an input reg file with  [x,y,comment] to a DS9 reg file.

        the input file should contain lines specifying x,y,comment

        Parameters
        ----------

        infile: str
            input filename

        labels: bool
            add labels to the regions

        header: int
            number of header lines in text file to skip

        textoff: int
            offset in pixels for labels

        size: int
            size of the region type


        Notes
        -----
        only circular regions are supported currently
        """
        try:
            f = open(infile, 'r')
            lines = f.readlines()
            f.close()

        except IOError as e:
            warnings.warn("Unable to open input file")
            print("{0}".format(e))
            raise ValueError

        # assumed defaults for simple regions file
        point = "circle"  # only one supported right now
        delta = textoff  # pixels to offset text
        lines = lines[header:]

        text = list()
        x = list()
        y = list()

        for i in range(0, len(lines), 1):
            words = lines[i].split(',')
            x.append(words[0].strip())
            y.append(words[1].strip())
            if(len(words) > 2 and labels):
                text.append(words[2].strip())

        # now write out to a reg file
        out = infile + ".reg"
        f = open(out, 'w')
        for i in range(0, len(lines), 1):
            pline = "image; " + point + \
                "(" + x[i] + "," + y[i] + "," + str(size) + ")\n"
            f.write(pline)
            if(len(text) > 0):
                pline = "image;text(" + str(float(x[i]) + delta) + "," + \
                    str(float(y[i]) + delta) + \
                    "{ " + text[i] + " })# font=\"time 12 bold\"\n"
                f.write(pline)
        f.close()

        print("output reg file saved to: {0:s}".format(out))

    def match(self, coordsys="wcs", frame=True, crop=False, fslice=False,
              scale=False, bin=False, colorbar=False, smooth=False,
              crosshair=False):
        """match all other frames to the current frame.

        Parameters
        ----------

        coordsys: string, optional
            The coordinate system to use

        frame: bool, optional
            Match all other frames to the current frame, using the set coordsys

        crop: bool, optional
            Set the current image display area, using the set coordsys

        fslice: bool, optional
            Match current slice in all frames

        scale: bool, optional
            Match to the current scale for all frames

        bin: bool, optional
            Match to the current binning for all frames

        colorbar: bool, optional
            Match to the current colorbar for all frames

        smooth: bool, optional
            Match to the current smoothing for all frames

        crosshair: bool, optional
            Match the crosshair in all frames, using the current coordsys


        Notes
        -----

        You can only choose one of the options at a time, and the logic will
        select the first True option so set frame=False and something else in
        addition to your choice if you don't want the default option.

        """
        cstring = "match "
        if frame:
            cstring += "frame {0:s}".format(coordsys)
        elif crosshair:
            cstring += "crosshair {0:s}".format(coordsys)
        elif crop:
            cstring += "crop {0:s}".format(coordsys)
        elif fslice:
            cstring += "slice"
        elif bin:
            cstring += "bin"
        elif scale:
            cstring += "scale"
        elif colorbar:
            cstring += "colorbar"
        elif smooth:
            cstring += "smooth"
        self.set(cstring)

    def nancolor(self, color="red"):
        """set the not-a-number color, default is red.

        Parameters
        ----------

        color: string
            The color to use for NAN pixels


        """
        self.set("nan {0:s}".format(color))

    def panto_image(self, x, y):
        """convenience function to change to x,y  physical image coordinates.

        Parameters
        ----------
        x: float
            X location in physical coords to pan to

        y: float
            Y location in physical coords to pan to

        """
        self.set("pan to {0:f} {1:f} image".format(x, y))

    def panto_wcs(self, x, y, system='fk5'):
        """pan to wcs location coordinates in image.

        Parameters
        ----------

        x: string
            The x location to move to, specified using the given system
        y: string
            The y location to move to
        system: string
            The reference system that x and y were specified in, they should
            be understood by DS9

        """
        self.set("pan to {0:s} {1:s} wcs {2:s}".format(x, y, system))

    def rotate(self, value=None, to=False):
        """rotate the current frame (in degrees).

        the current rotation is printed with no params

        Parameters
        ----------

        value: float [degrees]
            Rotate the current frame {value} degrees
            If value is 0, then the current rotation is printed

        to: bool
            Rotate the current frame to the specified value

        """
        if value is None:
            print("Image rotated at {0:s}".format(self.get("rotate")))

        elif to and value >= 0:
            cstring = "rotate to {0:s}".format(str(value))
            self.set(cstring)

        elif value > 0:
            cstring = "rotate {0:s}".format(str(value))
            self.set(cstring)
        cstring = "Image rotated at {0:s}".format(self.get("rotate"))
        print(cstring)
        logging.info(cstring)

    def save_regions(self, filename=None):
        """save the regions in the current window to a DS9 style regions file.

        Parameters
        ----------

        filename: string
            The nameof th file to which the regions displayed in the current
            window are saved. If no filename is provided then it will try and
            save the regions to the name of the file in the current display
            with _regions.txt appended

            If a file of that name already exists on disk it will no attempt
            to overwrite it

        """
        regions = self.get("regions save")
        frame = self.frame()

        if frame and not filename:
            filename = self._viewer[frame]['filename'] + "_regions.txt"

        # check if the file already exists
        if not os.access(filename, os.F_OK):
            with open(filename, "w") as region_file:
                region_file.write(regions)
        else:
            warnings.warn(
                "File already exists: {0} try again".format(filename))

    def save_rgb(self, filename=None):
        """save an rgbimage frame as an MEF fits file.

        Parameters
        ----------

        filename: string
            The name of the output fits image

        """
        if not filename:
            print("No filename specified, try again")
        else:
            self.set("save rgbimage {0:s}".format(filename))

    def scale(self, scale='zscale'):
        """The default zscale is the most widely used option.

        Parameters
        ----------
        scale: string
            The scale for ds9 to use, these are set strings of
            [linear|log|pow|sqrt|squared|asinh|sinh|histequ]

        Notes
        -----
        The xpa doesn't return an error if you set an unknown scale,
        it just doesn't do anything, this is true for all the xpa calls
        """
        _help = """Syntax:
           scales available: [linear|log|pow|sqrt|squared|asinh|sinh|histequ]

          [log exp <value>]
          [datasec yes|no]
          [limits <minvalue> <maxvalue>]
          [mode minmax|<value>|zscale|zmax]
          [scope local|global]
          [match]
          [lock [yes|no]]
          [open|close]

          """
        mode_scale = ["zscale", "zmax", "minmax"]
        cstring = "scale {0:s}".format(scale)

        if scale in mode_scale:
            cstring = "scale mode {0:s}".format(scale)
        try:
            self.set(cstring)
        except (XpaException, ValueError):
            print("{0:s} not valid".format(cstring))
            print(_help)

    def set_region(self, region_string=""):
        """display a region using the specifications in region_string.

        Parameters
        ----------

        region_string: string
            Should take the form of a region string that DS9 is expecting

        Examples
        --------
        set_region("physical ruler 200 300 200 400")
        set_region("line 0 400 3 400 #color=red")

        """
        command = "regions command {{ {0:s} }}\n".format(region_string)
        self.set(command)

    def showme(self):
        """raise the ds9 window."""
        self.set("raise")

    def showpix(self, close=False):
        """display the pixel value table, close window when done.

        Parameters
        ----------

        close: bool, optional
            If set to True, then the pixel table dialog window is closed


        """
        self.get("pixeltable")
        if close:
            self.set("pixeltable close")

    def snapsave(self, filename=None, format=None, resolution=100):
        """Create a snap shot of the current window, save in specified format.

        This function bypasses the XPA  calling routines to avoid a bug with
        the X11/XPA interface. Instead is uses the os import function which
        takes a snapshot of the specified x11 window.

        Parameters
        ----------

        filename: str, optional
           filename of output image, the extension in the filename can also be
           used to specify the format. If no filename is specified, then the
           filename will be constructed from the name of the image displayed
           image with _snap.png appended.

        format: str, optional
           available formats are fits, eps, gif, tiff, jpeg, png
           If no format is specified the filename extension is used

        resolution: int, optional
           1 to 100, for jpeg images

        """
        frame = self.frame()
        if not filename:
            filename = self._viewer[frame]['filename']

        if not format:
            filename += "_snap.png"
        else:
            filename += "_snap." + format

        cstring = ['import']
        cstring.append('-window ')
        # get the name of the window
        if "local" in self._xpa_method:
            win_name = self._xpa_name.split("DS9_")[1].split(".")
            newname = "SAOImage "
            newname += (".".join(win_name[0:2]))
            cstring.append(newname)
        else:
            cstring.append(self._xpa_name)

        if "jpeg" in filename:
            cstring.append(' -quality')
            cstring.append(str(resolution))

        cstring.append(filename)

        # self.set(cstring)
        # save the local directory, erase later?
        call(cstring)
        print("Image saved to {0:s}".format(filename))
        logging.info("Image saved to {0:s}".format(filename))
        return(filename)

    def grab(self):
        """Make a copy of the image view."""
        backend = get_backend().lower()
        fname = self.snapsave(format="png")
        if "nbagg" in backend:  # save inside the notebook
                data = mpimage.imread(fname)
                plt.clf()
                return plt.imshow(data, origin="upper")

    def view(self, img):
        """Display numpy image array to current frame.

        Parameters
        ----------
        img: numpy array
            The array containing data, it will be forced to numpy.array()

        """
        frame = self.frame()
        if not frame:
            print("No valid frame")
        else:
            img = np.array(img)
            if img.dtype.type == np.bool8:
                img = img.astype(np.uint8)

            try:
                img.shape = img.shape[-2:]
            except:
                raise UnsupportedImageShapeException(repr(img.shape))

            if img.dtype.byteorder in ["=", "|"]:
                dt = img.dtype.newbyteorder(">")
                img = np.array(img, dtype=dt)
                byteorder = ">"
            else:
                byteorder = img.dtype.byteorder

            endianness = {">": ",arch=bigendian",
                          "<": ",arch=littleendian"}[byteorder]
            (ydim, xdim) = img.shape
            arr_str = img.tostring()

            try:
                bitpix = self._ImgCode[img.dtype.name]
            except KeyError as e:
                raise UnsupportedDatatypeException(e)

            option = "[xdim={0:d},ydim={1:d},bitpix={2:d}{3:s}]".format(xdim,
                       ydim, bitpix, endianness)
            try:
                self.set("array " + option, arr_str)
                self._set_frameinfo()
                self._viewer[frame]['user_array'] = img
            except XpaException as e:
                raise XpaException(
                    "XPA: {0} : Problem loading array \
                    into frame {1}".format(e, frame))

    def zoomtofit(self):
        """Zoom to fit the image to the viewer."""
        self.zoom("to fit")

    def zoom(self, par="to fit"):
        """Zoom using the specified command.

        Parameters
        ----------
        par: string
            - it can be a number (ranging 0 to 8 effectively), and successive
                    calls continue zooming in the same direction
            - it can be two numbers '4 2', which specify zoom on different axis
            - if can be to a specific value 'to 8' or 'to fit'
            - it can be 'open' to open the dialog box
            - it can be 'close' to close the dialog box (only valid if the box
                    is already open)


        Examples
        --------
        zoom('0.1')

        """
        try:
            self.set("zoom {0:s}".format(str(par)))
        except XpaException:
            print(
                "XPA problem with zoom (probably your zoom \
                window is already closed)")

    def show_xpa_commands(self):
        """Print the available XPA commands."""
        print(self.get())  # with no arguments supplied, XPA returns options

    def reopen(self):
        """Reopen a closed window."""
        print("Not available for DS9, start a new object instead")
        raise NotImplementedError


atexit.register(ds9._purge_tmp_dirs)
atexit.register(ds9._stop_running_process)
