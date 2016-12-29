# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""This is the main controlling class, it allows the user to connect to
the viewer and the imexamine classes
"""

from __future__ import print_function, division, absolute_import

import warnings
import logging
import os
import astropy

from .util import set_logging
from .ds9_viewer import ds9
try:
    from .ginga_viewer import ginga
    have_ginga = True
except ImportError:
    have_ginga = False

from .imexamine import Imexamine

__all__ = ["Connect"]


class Connect(object):
    """Connect to a display device to look at and examine images.

    The control features below are a basic set that should be available
    in all display tools.

    The class for the display tool should override them and add it's own
    extra features.


    Parameters
    ----------

    target: string, optional
        the viewer target name or id (default is to start a new
        instance of a DS9 window)

    path : string, optional
        absolute path to the viewers executable

    viewer: string, optional
        The name of the image viewer you want to use, DS9 is the default

    wait_time: int, optional
        The time to wait for a connection to be eastablished before quitting

    Attributes
    ----------

    window: a pointer to an object
        controls the viewers functions

    imexam: a pointer to an object
        controls the imexamine functions and options

    """

    def __init__(self, target=None, path=None, viewer="ds9",
                 wait_time=10, quit_window=True, port=None):
        """Initialize the imexam control object."""
        # better dynamic way so people can add their own viewers?
        _possible_viewers = ["ds9"]

        self._viewer = viewer.lower()

        if have_ginga:
            _possible_viewers.append('ginga')

        if self._viewer not in _possible_viewers:
            warnings.warn("**Unsupported viewer, check your installed packages**\n")
            raise NotImplementedError

        # init sets empty data array until we can load or check viewer
        self.exam = Imexamine()

        if 'ds9' in self._viewer:
            self.window = ds9(
                target=target,
                path=path,
                wait_time=wait_time,
                quit_ds9_on_del=quit_window)
            self._event_driven_exam = False  # use the imexam loop

        elif 'ginga' in self._viewer:
            self.window = ginga(exam=self.exam,
                                close_on_del=quit_window,
                                port=port)
            # the viewer will track imexam with callbacks
            self._event_driven_exam = True

            # alter the exam.imexam_option_funcs{} here through the viewer code
            # if you want to change key+function associations
            # self.window._reassign_keys(imexam_dict)

        self.logfile = 'imexam_log.txt'  # default logfile name
        self.log = set_logging()  # points to the package logger
        self._current_slice = None
        self._current_frame = None

    def setlog(self, filename=None, on=True, level=logging.INFO):
        """Turn on and off logging to a logfile or the screen.

        Parameters
        ----------
        filename: str, optional
            Name of the  output file to record log information
        on: bool, optional
            True by default, turn the logging on or off
        level: logging class, optional
            set the level for logging messages, turn off screen messages
            by setting to logging.CRITICAL

        """
        if filename is not None:
            self.logfile = filename
        self.log = set_logging(self.logfile, on, level)

    def close(self):
        """Close the window and end connection."""
        # make sure all the plots are closed
        self.exam._close_plots()
        self.window.close()
        #  close any open  handlers for logging
        self.log = set_logging(on=False)

    def imexam(self):
        """Run imexamine loop with user interaction.

        At a minimum it requires a copy of the data array
        """
        if self.valid_data_in_viewer():
            if self._event_driven_exam:
                self._run_event_imexam()
            else:
                self._run_imexam()
        else:
            warnings.warn("No valid image loaded in viewer")

    def _run_event_imexam(self):
        """Let the viewer run an event driven imexam."""
        if not self._event_driven_exam:
            warnings.warn("Event driven imexam not implemented for viewer")
        else:
            self.exam.print_options()
            print("\nPress the i key in the graphics window for access \
                 to imexam keys, or q to exit\n")

    def reopen(self):
        """Reopen a display window closed by the user but not exited."""
        self.window.reopen()

    def grab(self):
        """Display a snapshop of the current image in the browser window."""
        return self.window.grab()

    def get_data_filename(self):
        """Return the filename for the data in the current window."""
        return self.window.get_filename()

    def valid_data_in_viewer(self):
        """Return True if a valid file or array is loaded."""
        return self.window.valid_data_in_viewer()

    def get_frame_info(self):
        """Return explicit information about the data displayed."""
        return self.window.get_frame_info()

    def get_viewer_info(self):
        """Return a dictionary with information about all frames with data."""
        return self.window.get_viewer_info()

    def _run_imexam(self):
        """Start imexam analysis loop for non event driven viewers.

        Notes
        -----
        The data displayed in the current frame is grabbed .The catch is that
        the user can change the data that is displayed using the gui menus in
        DS9, so during the imexam loop the display needs to be checked after
        each key stroke.

        This function will track the user changing the frame number using the
        gui display for  images and update the data array.

        ds9 returns 1-based, the problem comes with  printing the
        coordinates and visual comparison with what's displayed in the gui.
        The gui display seems to round up integer pixels at some zoom factors.
        I've set ds9 to return the 0 indexed location so that the numpy array
        is always correct.

        Verify this to some level by looking at the pixel returned and using
        the pixel table window in DS9 to look at surrounding values.

        imexamine() returns the value at the integer pixel location.
        """

        print("\nPress 'q' to quit\n")
        keys = self.exam.get_options()  # possible commands
        self.exam.print_options()
        cstring = "Current image {0}".format(self.get_data_filename(),)
        print(cstring)

        # set defaults
        self._current_frame = self.frame()
        if self.window.iscube():
            self._current_slice = self.window.get_slice_info()
        self.exam.set_data(self.window.get_data())
        current_key = keys[0]  # q is not in the list of keys

        while current_key:
            # ugly hack to suppress deprecation by mpl
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                self._check_frame()
                if self.window.iscube():
                    self._check_slice()
                try:
                    x, y, current_key = self.readcursor()
                    self._check_frame()
                    if self.window.iscube():
                        self._check_slice()
                    if current_key not in keys and 'q' not in current_key:
                        print("Invalid key")
                        self.exam._close_plots()
                    else:
                        if 'q' in current_key:
                            current_key = None
                            self.exam._close_plots()
                        else:
                            self.exam.do_option(
                                x, y, current_key)

                except KeyError:
                    print(
                        "Invalid key, use\n: {0}".format(
                            self.exam.print_options()))
                    self.exam._close_plots()

    def _check_frame(self):
        """check if the user switched frames.

        This can happen when using DS9 because the user has
        access to the gui controls while the imexam loop is
        running.
        """
        frame = self.frame()
        if self._current_frame != frame:  # the user has changed window frames
            self.exam.set_data(self.window.get_data())
            self._current_frame = frame
            try:
                cstring = "\nCurrent image {0:s}".format(
                        self.get_frame_info()['filename'],)
            except TypeError:
                cstring = "\nuser array in frame"
            self.log.info(cstring)
            print(cstring)

    def _check_slice(self):
        """check if the user switched slice images."""
        this_slice = self.window.get_slice_info()
        if self._current_slice != this_slice:
            self.exam.set_data(self.window.get_data())
            self._current_slice = this_slice
            cstring = "\nCurrent slice {0:s}".format(
                self.get_frame_info()['naxis'],)
            self.log.info(cstring)
            print(cstring)

    #  Implement the following functions in your viewer class

    def readcursor(self):
        """Return the image coordinate postion and key pressed.

        in the form of x,y,str with array offset
        """
        return self.window.readcursor()

    def alignwcs(self, **kwargs):
        """Align frames with wcs."""
        self.window.alignwcs(**kwargs)

    def blink(self, **kwargs):
        """Blink windows if available."""
        self.window.blink(**kwargs)

    def clear_contour(self):
        """Clear contours on window if available."""
        self.window.clear_contour()

    def cmap(self, **kwargs):
        """Set the color map table to something else.

        Should verify with a defined list of options
        """
        self.window.cmap(**kwargs)

    def colorbar(self, **kwargs):
        """Turn the colorbar on the screen on and off."""
        self.window.colorbar(**kwargs)

    def contour(self, **kwargs):
        """Show contours on the window."""
        self.window.contour(**kwargs)

    def contour_load(self, *args):
        """Load contours from a file."""
        self.window.contour_load(*args)

    def crosshair(self, **kwargs):
        """Control the current position of the crosshair in the current frame.

        crosshair mode is turned on by default
        """
        self.window.crosshair(**kwargs)

    def cursor(self, **kwargs):
        """Move the cursor in the current frame to the specified image pixel.

        it will also move selected regions
        """
        self.window.cursor(**kwargs)

    def disp_header(self, **kwargs):
        """Display the header of the current image to a window."""
        self.window.disp_header()

    def embed(self, **kwargs):
        return self.window.embed(**kwargs)

    def frame(self, *args, **kwargs):
        """Move to a different frame."""
        return self.window.frame(*args, **kwargs)

    def get_data(self):
        """Return a numpy array of the data in the current window."""
        return self.window.get_data()

    def get_image(self):
        """Return the full image object, not just the numpy array."""
        return self.window.get_image()

    def get_header(self, **kwargs):
        """Return the current fits header as a string.

        None is returned if there's a problem
        """
        return self.window.get_header(**kwargs)

    def grid(self, *args, **kwargs):
        """Convenience method to turn the grid on and off.

        grid can be flushed with many more options
        """
        self.window.grid(*args, **kwargs)

    def hideme(self):
        """Lower the precedence of the display window."""
        self.window.hideme()

    def load_fits(self, *args, **kwargs):
        """Convenience function to load fits image to current frame."""
        if 'fname' in kwargs.keys():
            self.exam._datafile = kwargs['fname']
        else:
            self.exam._datafile = args[0]
        self.window.load_fits(*args, **kwargs)

    def load_region(self, *args, **kwargs):
        """Load regions from a file which uses standard formatting."""
        self.window.load_region(*args, **kwargs)

    def load_mef_as_cube(self, *args, **kwargs):
        """Load a Mult-Extension-Fits image one frame as a cube."""
        self.window.load_mef_as_cube(*args, **kwargs)

    def load_mef_as_multi(self, *args, **kwargs):
        """Load a Mult-Extension-Fits image into multiple frames."""
        self.window.load_mef_as_multi(*args, **kwargs)

    def make_region(self, *args, **kwargs):
        """Make an input reg file with [x,y,comment] to a standard reg file.

        the input file should contains lines with x,y,comment
        """
        self.window.make_region(*args, **kwargs)

    def mark_region_from_array(self, *args, **kwargs):
        """Mark regions on the viewer with a list of tuples as input."""
        self.window.mark_region_from_array(*args, **kwargs)

    def match(self, **kwargs):
        """Match all other frames to the current frame."""
        self.window.match(**kwargs)

    def nancolor(self, **kwargs):
        """Set the not-a-number (NaN) color."""
        self.window.nancolor(**kwargs)

    def panto_image(self, *args, **kwargs):
        """Convenience function to change to x,y images coordinates.

        using ra,dec, x, y in image coord
        """
        self.window.panto_image(*args, **kwargs)

    def panto_wcs(self, *args, **kwargs):
        """Pan to wcs coordinates in image."""
        self.window.panto_wcs(*args, **kwargs)

    def load_rgb(self, *args, **kwargs):
        """Load three images into a frame, each one for a different color."""
        self.window.load_rgb(*args, **kwargs)

    def rotate(self, *args, **kwargs):
        """Rotate the current frame (in degrees)."""
        self.window.rotate(*args, **kwargs)

    def save_rgb(self, *args, **kwargs):
        """Save an rgb image frame that is displayed as an MEF fits file."""
        self.window.save_rgb(*args, **kwargs)

    def save_header(self, *args, **kwargs):
        """Save the header of the current image to a file."""
        self.window.save_header(*args, **kwargs)

    def save_regions(self, *args, **kwargs):
        """Save the regions on the current window to a file."""
        self.window.save_regions(*args, **kwargs)

    def scale(self, *args, **kwargs):
        """Scale the image on display.

        The default zscale is the most widely used option
        """
        self.window.scale(*args, **kwargs)

    def set_region(self, *args, **kwargs):
        """Display a region using the specifications in region_string."""
        self.window.set_region(*args, **kwargs)

    def showme(self):
        """Raise the precedence of the display window."""
        self.window.showme()

    def showpix(self, *args, **kwargs):
        """Display the pixel value table, close window when done."""
        self.window.showpix(*args, **kwargs)

    def show_window_commands(self):
        """Print the available commands for the selected display window."""
        return [k for k in dir(self.window) if "_" not in k]

    def snapsave(self, *args, **kwargs):
        """Create a snap shot of the current window.

        save in the specified format.
        If no format is specified the filename extension is used
        """
        self.window.snapsave(*args, **kwargs)

    def view(self, *args, **kwargs):
        """Display numpy or nddata image array.

        If an astropy NDData object is passed without a reference to the data
        one will be added. I haven't tested this yet for multiarray data
        """
        self.exam._datafile = "array"
        if isinstance(args[0], astropy.nddata.nddata.NDData):
            self.window.view(args[0].data)  # when not specified
        else:
            self.window.view(*args, **kwargs)

    def zoom(self, *args, **kwargs):
        """Zoom to parameter which can be any recognized string."""
        self.window.zoom(*args, **kwargs)

    def zoomtofit(self):
        """Zoom the image to fit the display."""
        self.window.zoomtofit()

    def _get_function_name(self, key=None):
        """Return the function and parname associated with the key."""
        if key is None:
            print("You need to specify the key-name for the function")
            return None
        if key in self.exam._reserved_keys:
            print("{0:s} is reserved".format(key))
            return None
        if key not in self.exam.imexam_option_funcs:
                print("Key not available")
                return None
        fname = self.exam.imexam_option_funcs[key][0].__name__
        parname = fname + "_pars"
        return fname, parname

    def set_plot_pars(self, key=None, item=None, value=None):
        """Set the chosen plot parameter with the provided value.

        Parameters
        ----------

        key: String
            The value of the option key, should be a single letter or number

        item: string
            The value of the parameter in the dictionary

        value: float, string, int, bool
            What the parameters value should be set to

        Examples
        --------
        set_plot_par('j','func','MexicanHat1D')

        where j is the key value during imexam
        func is the parameter you want to edit
        MexicanHat1D is the name of the astropy function to use

        """
        fname, parname = self._get_function_name(key)
        if parname:
            current_dict = self.exam.__getattribute__(parname)
        else:
            print("No information for parameters available")
            return
        if item not in current_dict:
            print("No parameter of that name in dictionary")
            return
        else:
            current_dict[item][0] = value
            print("set {0}: {1} to {2}".format(parname, item, value))
            return

    def aimexam(self, get_name=False):
        """Show the current parameters for the 'a' key.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['a'][0].__name__
        else:
            return(self.exam.aper_phot_pars)

    def cimexam(self, get_name=False):
        """Show the current parameters for the 'c' key.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['c'][0].__name__
        else:
            return(self.exam.colplot_pars)

    def eimexam(self, get_name=False):
        """Show the current parameters for the 'e' key, returns dict."""
        if get_name:
            return self.exam.imexam_option_funcs['e'][0].__name__
        else:
            return(self.exam.contour_pars)

    def himexam(self, get_name=False):
        """Show the current parameters for 'h' key, returns dict.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['h'][0].__name__
        else:
            return(self.exam.histogram_pars)

    def jimexam(self, get_name=False):
        """Show the current parameters for 1D fit line plots, returns dict.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['j'][0].__name__
        else:
            return(self.exam.line_fit_pars)

    def kimexam(self, get_name=False):
        """Show the current parameters for 1D fit column plots, returns dict.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['k'][0].__name__
        else:
            return(self.exam.column_fit_pars)

    def limexam(self, get_name=False):
        """Show the current parameters for  line plots, returns dict.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['l'][0].__name__
        else:
            return(self.exam.lineplot_pars)

    def mimexam(self, get_name=False):
        """Show the current parameters for statistical regions, returns dict.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['m'][0].__name__
        else:
            return(self.exam.report_stat_pars)

    def gimexam(self, get_name=False):
        """Show the current parameters for curve of growth plots, returns dict.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['g'][0].__name__
        else:
            return(self.exam.curve_of_growth_pars)

    def rimexam(self, get_name=False):
        """Show the current parameters for curve of growth plots, returns dict.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['r'][0].__name__
        else:
            return(self.exam.radial_profile_pars)

    def wimexam(self, get_name=False):
        """Show the current parameters for surface plots, returns dict.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['w'][0].__name__
        else:
            return(self.exam.surface_pars)

    def timexam(self, get_name=False):
        """Show current parameters for image cutouts,returns dict.

        Either returns the name of the function associated with the keyname
        Or it returns the dictionary of plotting parameters for that key
        """
        if get_name:
            return self.exam.imexam_option_funcs['t'][0].__name__
        else:
            return(self.exam.cutout_pars)

    def unlearn(self):
        """Unlearn all the imexam parameters and reset to default."""
        self.exam.unlearn_all()

    def plotname(self, filename=None):
        """Change or show the default save plotname for imexamine."""
        if filename is None:
            self.exam.get_plot_name()  # show the current default
        else:
            if os.access(filename, os.F_OK):
                warnings.warn(
                    "File with that name already exists:{0s}".format(filename))
            else:
                self.exam.set_plot_name(filename)
