"""Licensed under a 3-clause BSD style license - see LICENSE.rst

   This class supports communication with a Ginga-based viewer.
   For default key and mouse shortcuts in a Ginga window, see:
   https://ginga.readthedocs.org/en/latest/quickref.html
"""
from __future__ import print_function, division, absolute_import

import sys
import os
import traceback
import warnings
import threading
import numpy as np

from . import util
from astropy.io import fits

from ginga.misc import log, Settings
from ginga.AstroImage import AstroImage
from ginga.BaseImage import BaseImage
from ginga import cmap
from ginga.util import paths
from ginga.util import wcsmod


wcsmod.use('AstropyWCS')

# module variables
_matplotlib_cmaps_added = False

# the html5 viewer is currently supported as ginga
# this can be used from the python commandline or
# inside a jupyter notebook
__all__ = ['ginga', 'ginga_general']


class ginga_general(object):

    """ A base class which controls all interactions between the user and the
    ginga widget.

    The ginga contructor creates a new window using the
    ginga backend.

    Parameters
    ----------
    close_on_del : boolean, optional
        If True, try to close the window when this instance is deleted.


    Attributes
    ----------
    view: Ginga view object
         The object instantiated from a Ginga view class

    exam: imexamine object
    """

    def __init__(self, exam=None, close_on_del=True, logger=None, port=None):
        """initialize a general ginga viewer object.

        Parameters
        ----------

        exam: imexam object
            This is the imexamine object which contains the examination
            functions

        close_on_del: bool
            If True, the window connection shuts down when the object is
            deleted

        logger: logger object
            Ginga viewers all need a logger, if none is provided it will
            create one

        port: int
            This is used as the communication port for the HTML5 viewer. The
            user can choose to have multiple windows open at the same time
            as long as they have different port designations. If no port is
            specified, this class will choose an open port.

        """
        global _matplotlib_cmaps_added
        self._port = port
        self.exam = exam
        self._close_on_del = close_on_del
        # dictionary where each key is a frame number, and the values are a
        # dictionary of details about the image loaded in that frame
        self._viewer = dict()
        self._current_frame = 1
        self._current_slice = None

        # ginga view object, created in subclass
        self.ginga_view = None

        # set up possible color maps
        self._define_cmaps()

        # for synchronizing on keystrokes
        self._rlock = threading.RLock()  # this creates a thread lock
        self._keyvals = list()
        self._capturing = False

        # ginga objects need a logger, create a null one if we are not
        # handed one in the constructor
        self._log_level = 40
        if logger is None:
            logger = log.get_logger(level=self._log_level, log_stderr=True)
        self.logger = logger

        # Establish settings (preferences) for ginga viewers
        basedir = paths.ginga_home
        self.prefs = Settings.Preferences(
            basefolder=basedir,
            logger=self.logger)

        # general preferences shared with other ginga viewers
        self.settings = self.prefs.createCategory('general')
        self.settings.load(onError='silent')
        self.settings.setDefaults(useMatplotlibColormaps=False,
                                  autocuts='on', autocut_method='zscale')

        # add matplotlib colormaps to ginga's own set if user has this
        # preference set
        if self.settings.get('useMatplotlibColormaps', False) and \
                (not _matplotlib_cmaps_added):
            # Add matplotlib color maps if matplotlib is installed
            try:
                cmap.add_matplotlib_cmaps()
                _matplotlib_cmaps_added = True
            except Exception as e:
                print(
                    "Failed to load matplotlib colormaps: {0}".format(
                        repr(e)))

        # bindings preferences shared with other ginga viewers
        bind_prefs = self.prefs.createCategory('bindings')
        bind_prefs.load(onError='silent')

        # viewer preferences unique to imexam ginga viewers
        viewer_prefs = self.prefs.createCategory('imexam')
        viewer_prefs.load(onError='silent')

        # create the viewer specific to this backend
        self._create_viewer(bind_prefs, viewer_prefs)

        # TODO: at some point, it might be better to simply add a custom
        # mode called "imexam"--that is a more robust way to do things
        # but we'd have to register the imexam key bindings in a different way
        # bm = self.ginga_view.get_bindmap()
        # bm.add_mode('i', 'imexam', mode_type='locked',
        #             msg="Entering imexam mode...")
        # modifiers_set = bindmap.get_modifiers()
        # bm.map_event('imexam', modifiers_set, trigger, evname)

        # enable all interactive ginga features
        bindings = self.ginga_view.get_bindings()
        bindings.enable_all(True)

        # Add a callback to take us into imexam mode
        top_canvas = self.ginga_view.get_canvas()
        top_canvas.add_callback('key-press', self._key_press_normal)

        # Add a callback to our private canvas to take us out of imexam mode
        self.canvas.enable_draw(False)
        self.canvas.add_callback('key-press', self._key_press_imexam)
        self.canvas.set_surface(self.ginga_view)
        self.canvas.ui_setActive(True)

    def _create_viewer(self, bind_prefs, viewer_prefs):
        """Create backend-specific viewer."""
        raise Exception("Subclass should override this method!")

    def _capture(self):
        """Insert our imexam canvas so that we intercept all events.

        before they reach processing by the bindings layer of Ginga.
        """
        self.ginga_view.onscreen_message("Entering imexam mode",
                                         delay=1.0)
        top_canvas = self.ginga_view.get_canvas()
        top_canvas.add(self.canvas, tag='imexam-canvas')
        self._capturing = True

    def _release(self):
        """Remove our canvas so that we no longer intercept events."""

        self.ginga_view.onscreen_message("Leaving imexam mode",
                                         delay=1.0)
        self._capturing = False
        top_canvas = self.ginga_view.get_canvas()
        top_canvas.delete_object_by_tag("imexam-canvas")
        self.logger.debug("canvas deleted top=%s" % top_canvas.objects)

    def __str__(self):
        """Return viewer name."""
        return "<imexam viewer>"

    def __del__(self):
        """Close the viewer."""
        if self._close_on_del:
            self.close()

    def _set_frameinfo(self, fname=None, hdu=None, data=None,
                       image=None):
        """Set the name and extension information for the data displayed.

        Parameters
        ----------
        fname: string
            The filename of the image

        hdu: int
            The extension to pull the image from

        data: numpy array
            if data is specified, then the array is used instead of the file

        image: AstroImage object
            Image object taken from Ginga

        Notes
        -----
        This function also gathers important image header information.
        This function may need some more update to make it uniform for
        the package.
        """
        # check the current frame, if none exists, then don't continue
        frame = self._current_frame
        if frame:
            if frame not in self._viewer.keys():
                self._viewer[self._current_frame] = dict()

            if data is None or not data.any():
                try:
                    data = self._viewer[self._current_frame]['user_array']
                except KeyError:
                    pass

            extver = None  # extension number
            extname = None  # name of extension
            numaxis = 2  # number of image planes, this is NAXIS
            # tuple of each image plane, defaulted to 1 image plane
            naxis = (0)
            # data has more than 2 dimensions and loads in cube/slice frame
            iscube = False
            mef_file = False  # used to check misleading headers in fits files

            if hdu:
                pass

            # update the viewer dictionary, if the user changes what's
            # displayed in a frame this should update correctly
            # this dictionary will be referenced in the other parts of the
            # code. This enables tracking user arrays through frame changes

            self._viewer[self._current_frame] = {'filename': fname,
                                                 'extver': extver,
                                                 'extname': extname,
                                                 'naxis': naxis,
                                                 'numaxis': numaxis,
                                                 'iscube': iscube,
                                                 'user_array': data,
                                                 'image': image,
                                                 'hdu': hdu,
                                                 'mef': mef_file}

    def valid_data_in_viewer(self):
        """Return bool if a valid file or array is loaded into the viewer"""
        frame = self._current_frame

        if self._viewer[frame]['filename']:
            return True
        else:
            try:
                if self._viewer[frame]['user_array'].any():
                    valid = True
                elif self._viewer[frame]['hdu'].any():
                    valid = True
                elif self._viewer[frame]['image'].any():
                    valid = True
            except AttributeError as ValueError:
                valid = False
                print("error in array")

            return valid

    def get_filename(self):
        """Return the filename currently associated with the data"""
        frame = self.frame()
        if frame:
            return self._viewer[frame]['filename']

    def get_frame_info(self):
        """Return more explicit information about the data in current frame."""
        return self._viewer[self.frame()]

    def get_viewer_info(self):
        """Return a dictionary of information about all frames with data"""
        return self._viewer

    def close(self):
        """Close the window."""
        raise NotImplementedError

    def start_event_loop(self):
        pass

    def readcursor(self):
        """Returns image coordinate postion and key pressed."""
        # insert canvas to trap keyboard events if not already inserted
        if not self._capturing:
            self._capture()

        with self._rlock:
            self._keyvals = ()

        # wait for a key press
        # NOTE: the viewer now calls the functions directly from the
        # dispatch table, and only returns on the quit key here
        while True:
            # ugly hack to suppress deprecation  by mpl
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # run event loop, so window can get a keystroke
                # but only depending on context
                if self.use_opencv():
                    self.canvas.start_event_loop(timeout=0.1)

            with self._rlock:
                # did we get a key event?
                if len(self._keyvals) > 0:
                    (k, x, y) = self._keyvals
                    print("key pressed:{0:s} on x:{1} y:{2}".format(k, x, y))
                    break

        # ginga is returning 0 based indexes
        return x, y, k

    def _define_cmaps(self):
        """Setup the default color maps which are available."""

        # get ginga color maps
        self._cmap_colors = cmap.get_names()

    def cmap(self, color=None, load=None, invert=False, save=False,
             filename='colormap.ds9'):
        """Set the color map table to something else, using a defined list of options.


        Parameters
        ----------
        color: string
            color must be set to one of the available color map names

        load: string, optional
            set to the filename which is a valid colormap lookup table
            valid contrast values are from 0 to 10, and valid bias values are
            from 0 to 1

        invert: bool, optional
            invert the colormap

        save: bool, optional
            save the current colormap as a file

        filename: string, optional
            the name of the file to save the colormap to

        """

        if color:
            if color in self._cmap_colors:
                self.ginga_view.set_color_map(color)
            else:
                print("Unrecognized color map, choose one of these:")
                print(self._cmap_colors)

        # these should be pretty easy to support if we use matplotlib
        # to load them
        if invert:
            warnings.warn("Colormap invert not supported")

        if load:
            warnings.warn("Colormap loading not supported")

        if save:
            warnings.warn("Colormap saving not supported")

    def frame(self):
        """Convenience function to report frames.

        currently only 1 frame is supported per calling object in HTML5 display
        """
        return self._current_frame

    def iscube(self):
        """Return whether a cube image is displayed in the current frame."""
        if self._current_frame:
            return self._viewer[self._current_frame]['iscube']

    def get_slice_info(self):
        """Return the slice tuple that is currently displayed."""
        frame = self._current_frame

        if self._viewer[frame]['iscube']:
            image_slice = self._viewer[frame]['naxis']
        else:
            image_slice = None
        return image_slice

    def get_data(self):
        """Return a numpy array of the data displayed in the current frame

        Notes
        -----
        This is the data array that the imexam() function from connect() uses
        for analysis

        astropy.io.fits stores data in row-major format. So a 4d image would be
        [NAXIS4, NAXIS3, NAXIS2, NAXIS1] just the one image is retured in the
        case of multidimensional data, not the cube

        """

        frame = self._current_frame
        if frame:
            if isinstance(self._viewer[frame]['user_array'], np.ndarray):
                return self._viewer[frame]['user_array']
            if isinstance(self._viewer[frame]['user_array'], BaseImage):
                return self._viewer[frame]['user_array'].get_data()
            if isinstance(self._viewer[frame]['image'], AstroImage):
                return self._viewer[frame]['image'].get_data()
        else:
            return None

    def get_image(self):
        """Return the AstroImage instance for the data in the viewer"""
        frame = self._current_frame
        if frame:
            if isinstance(self._viewer[frame]['user_array'], np.ndarray):
                print("Data is just a numpy array")
                return self._viewer[frame]['user_array']
            if isinstance(self._viewer[frame]['user_array'], BaseImage):
                return self._viewer[frame]['user_array']
            if isinstance(self._viewer[frame]['image'], AstroImage):
                return self._viewer[frame]['image']
        else:
            return None

    def contour_load(self):
        """Load a file with contour information."""
        raise NotImplementedError

    def disp_header(self):
        """Display the fits header for the current data."""
        self.get_header()

    def get_header(self):
        """Return current fits header as string, None if there's a problem."""

        # TODO return the simple header for arrays which are loaded

        frame = self._current_frame
        if frame and self._viewer[frame]['hdu'] is not None:
            hdu = self._viewer[frame]['hdu']
            return hdu.header
        else:
            warnings.warn("No file with header loaded into ginga")
            return None

    def _set_log_level(self, level):
        """Set the logging level."""
        self.logger.setLevel(level)
        # Because levels are settable at each handler, we have to run
        # through the handlers to set them as well.
        # Ugh...no logging API for getting handlers!
        for hdlr in self.logger.handlers:
            hdlr.setLevel(level)

    def _key_press_normal(self, canvas, keyname):
        """Callback function for keypress in ginga with no canvas overlay.

        This callback function is called when a key is pressed in the
        ginga window without the canvas overlaid.  It's sole purpose is to
        recognize an 'i' to put us into 'imexam' mode.
        """
        if keyname == 'i':
            self._capture()
            return True
        return False

    def _key_press_imexam(self, canvas, keyname):
        """Callback function for keypress in ginga with canvas overlay.

        This callback function is called when a key is pressed in the
        ginga window with the canvas overlaid.  It handles all the
        dispatch of the 'imexam' mode.
        """
        data_x, data_y = self.ginga_view.get_last_data_xy()

        if "q" not in keyname:
            print("read: {0:s} at {1}, {2}".format(keyname, data_x, data_y))

        self.logger.debug("key %s pressed at data %f,%f" % (
            keyname, data_x, data_y))

        if keyname == 'q':
            # temporarily switch to non-imexam mode
            self._release()
            self.exam._close_plots()
            return True

        if keyname == 'backslash':
            # exchange normal logger for the stdout debug logger
            log_debug = (self._log_level == 10)
            if not log_debug:
                self._log_level = 10
                self._set_log_level(self._log_level)
                self.ginga_view.onscreen_message("Debug logging on",
                                                 delay=1.0)
            else:
                self._log_level = 60
                self._set_log_level(self._log_level)
                self.ginga_view.onscreen_message("Debug logging off",
                                                 delay=1.0)
        data = self.get_data()

        # this will be picked up by the caller in readcursor()
        self._keyvals = (keyname, data_x, data_y)
        with self._rlock:
            self.logger.debug(
                "x,y,data dim: %f %f %i" %
                (data_x, data_y, data.ndim))
            self.logger.debug("exam=%s" % str(self.exam))

            # call the imexam function directly
            self.logger.debug(
                "calling examine function key={0}".format(keyname))
            try:
                method = self.exam.imexam_option_funcs[keyname][0]
            except KeyError:
                return False
            try:
                method(data_x, data_y, data)
            except Exception as e:
                self.logger.error("Failed examine function: %s" % (repr(e)))
                try:
                    # log traceback, if possible
                    (type, value, tb) = sys.exc_info()
                    tb_str = "".join(traceback.format_tb(tb))
                    self.logger.error("Traceback:\n%s" % (tb_str))
                except Exception:
                    tb_str = "Traceback information unavailable."
                    self.logger.error(tb_str)

            return True

    def embed(self, width=600, height=650):
        """Embed the current window into the notebook."""

        return self.ginga_view.embed(width, height)

    def load_fits(self, fname="", extver=None, extname=None):
        """Load fits image to current frame.

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

        Notes
        -----
        Extname isn't really used here, ginga wants the absolute extension
        number, not the version number associated with a name
        """
        if fname is None:
            raise ValueError("No filename provided")

        try:
            shortname, extn, extv = util.verify_filename(fname)
            image = AstroImage(logger=self.logger)

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

            with fits.open(shortname) as filedata:
                hdu = filedata[extver]
                image.load_hdu(hdu)

        except Exception as e:
            self.logger.error("Exception opening file: {0}".format(repr(e)))
            raise Exception(repr(e))

        self._set_frameinfo(fname=shortname, hdu=hdu, image=image)
        self.ginga_view.set_image(image)

    def panto_image(self, x, y):
        """Change to x,y  physical image coordinates.


        Parameters
        ----------
        x: float
            X location in physical coords to pan to

        y: float
            Y location in physical coords to pan to


        """
        # ginga deals in 0-based coords
        x, y = x - 1, y - 1

        self.ginga_view.set_pan(x, y)

    def panto_wcs(self, x, y, system='fk5'):
        """Pan to wcs location coordinates in image


        Parameters
        ----------

        x: string
            The x location to move to, specified using the given system
        y: string
            The y location to move to
        system: string
            The reference system that x and y were specified in, they should be
            understood by DS9

        """
        # this should be replaced by querying our own copy of the wcs
        image = self.ginga_view.get_image()
        a, b = image.radectopix(x, y, coords='data')
        self.ginga_view.set_pan(a, b)

    def rotate(self, value=None):
        """Rotate the current frame (in degrees).

        the current rotation is printed with no params

        Parameters
        ----------

        value: float [degrees]
            Rotate the current frame {value} degrees
            If value is None, then the current rotation is printed

        """
        if value is not None:
            self.ginga_view.rotate(value)

        rot_deg = self.ginga_view.get_rotation()
        print("Image rotated at {0:f} deg".format(rot_deg))

    def transform(self, flipx=None, flipy=None, swapxy=None):
        """Transform the frame.

        Parameters
        ----------

        flipx: boolean
            if True flip the X axis, if False don't, if None leave current
        flipy: boolean
            if True flip the Y axis, if False don't, if None leave current
        swapxy: boolean
            if True swap the X and Y axes, if False don't, if None leave
            current
        """
        _flipx, _flipy, _swapxy = self.ginga_view.get_transform()

        # preserve current transform if not supplied as a parameter
        if flipx is None:
            flipx = _flipx
        if flipy is None:
            flipy = _flipy
        if swapxy is None:
            swapxy = _swapxy

        self.ginga_view.transform(flipx, flipy, swapxy)

    def snapsave(self):
        """Save a frame display as a PNG file.

        Parameters
        ----------

        filename: string
            The name of the output PNG image

        """
        self.ginga_view.show()

    def scale(self, scale='zscale'):
        """Scale the image intensity, zscale is used as the default.

        Parameters
        ----------

        scale: string
            The scale for ds9 to use, these are set strings of
            [linear|log|pow|sqrt|squared|asinh|sinh|histequ]

        """

        if isinstance(scale, tuple):
            self.ginga_view.scale_to(scale)

        elif isinstance(scale, str):
            # setting the autocut method?
            mode_scale = self.ginga_view.get_autocut_methods()

            if scale in mode_scale:
                self.ginga_view.set_autocut_params(scale)

            # setting the color distribution algorithm?
            color_dist = self.ginga_view.get_color_algorithms()

            if scale in color_dist:
                self.ginga_view.set_color_algorithm(scale)
        else:
            print("Unknown scale value")

    def view(self, img):
        """Display numpy image array in current frame

        Parameters
        ----------
        img: numpy array
            The array containing data, it will be forced to numpy.array()

        Examples
        --------
        view(np.random.rand(100,100))

        """

        frame = self.frame()
        if not frame:
            print("No valid frame")
        else:
            img_np = np.array(img)
            image = BaseImage(data_np=img_np, logger=self.logger)
            self._set_frameinfo(data=img_np, image=image)
            self.ginga_view.set_image(image)

    def zoomtofit(self):
        """Zoom the image to fit the display."""
        self.ginga_view.zoom_fit()

    def zoom(self, zoomlevel):
        """Zoom the image using the specified zoomlevel.

        Parameters
        ----------
        zoomlevel: integer

        Examples
        --------
        zoom(6)
        zoom(-3)

        """

        try:
            self.ginga_view.zoom_to(zoomlevel)

        except Exception as e:
            print("problem with zoom: %s" % repr(e))

    def blink(self):
        """Blink multiple frames."""
        raise NotImplementedError

    def crosshair(self, **kwargs):
        """Control the current position of the crosshair in the frame.

        crosshair mode is turned on."""
        raise NotImplementedError

    def cursor(self, **kwargs):
        """Move the cursor in the current frame to the specified image pixel.

        it will also move selected regions"""
        raise NotImplementedError

    def grid(self, *args, **kwargs):
        """Turn the grid display on and off.

        grid can be flushed with many more options"""
        raise NotImplementedError

    def hideme(self):
        """Lower the display window in prededence."""
        raise NotImplementedError

    def load_region(self, *args, **kwargs):
        """Load regions from a file which uses standard formatting."""
        raise NotImplementedError

    def load_mef_as_cube(self, *args, **kwargs):
        """Load a Mult-Extension-Fits image one frame as a cube."""
        raise NotImplementedError

    def load_mef_as_multi(self, *args, **kwargs):
        """Load a Mult-Extension-Fits image into multiple frames."""
        raise NotImplementedError

    def make_region(self, *args, **kwargs):
        """make an input reg file with  [x,y,comment] to a standard reg file.

        the input file should contains lines with x,y,comment"""
        raise NotImplementedError

    def mark_region_from_array(self, *args, **kwargs):
        """Mark regions on the viewer with a list of tuples as input."""
        raise NotImplementedError

    def match(self, **kwargs):
        """Match all other frames to the current frame."""
        raise NotImplementedError

    def nancolor(self, **kwargs):
        """Set the not-a-number (Nan) color."""
        raise NotImplementedError

    def load_rgb(self, *args, **kwargs):
        """Load three images into a frame, each one for a different color."""
        raise NotImplementedError

    def save_rgb(self, *args, **kwargs):
        """Save an rgb image frame that is displayed as an MEF fits file."""
        raise NotImplementedError

    def save_header(self, *args, **kwargs):
        """Save the header of the current image to a file."""
        raise NotImplementedError

    def save_regions(self, *args, **kwargs):
        """Save the displayed regions on the current window to a file."""
        raise NotImplementedError

    def set_region(self, *args, **kwargs):
        """Display a region using the specifications in region_string."""
        raise NotImplementedError

    def showme(self):
        """Raise the precendence of the display window."""
        raise NotImplementedError

    def showpix(self, *args, **kwargs):
        """Display the pixel value table, closing the window when done."""
        raise NotImplementedError

    def show_window_commands(self):
        """Print the available commands for the selected display."""
        raise NotImplementedError

    def grab(self):
        # if self.ginga_view:
        return self.ginga_view.show()


class ginga(ginga_general):
    """A ginga-based viewer that displays to an HTML5 widget in a browser.

    This is compatible with the Jupyter notebook and can be run from a server.

    This kind of viewer has slower performance than if we
    choose some widget back ends, but the advantage is that
    it works so long as the user has a working browser.

    All the rendering is done on the server side and the browser only acts as
    a display front end.  Using this you could create an analysis type
    environment on a server and view it via a browser or from a
    Jupyter notebook.
    """

    def __init__(self, exam=None, close_on_del=True, logger=None, port=None,
                 host='localhost', use_opencv=False):

        # Set this to True if you have a non-buggy python OpenCv bindings
        #   --it greatly speeds up some operations
        self.use_opencv = use_opencv
        self._host = host
        self._server = None
        self._port = port

        super(ginga, self).__init__(exam=exam, close_on_del=close_on_del,
                                    logger=logger, port=self._port)

    def _open_browser(self):
        """Called as part of the viewer creation to open a browser."""
        try:
            import webbrowser
            webbrowser.open_new_tab(self.ginga_view.url)
        except ImportError:
            warnings.warn(
                "webbrowser module not installed, see the installed \
                doc directory for the HTML help pages")
            print("Open a new browser window for: {}".format(self.ginga_view.url()))

    def _create_viewer(self, bind_prefs, viewer_prefs,
                       opencv=False, threads=1):
        """Ginga setup for data display in an HTML5 browser."""
        from ginga.web.pgw import Widgets

        # Set opencv to True if you have a non-buggy python OpenCv bindings
        # --it greatly speeds up some operations
        self.use_opencv = opencv
        self._threads = threads
        self._server = None
        self._start_server()

        self.ginga_view = self._server.get_viewer('Imexam Display')

        # pop up a separate browser window with the viewer
        self._open_browser()

        # create a canvas that we insert when doing imexam mode
        top_canvas = self.ginga_view.get_canvas()
        self.canvas = top_canvas.get_draw_class('drawingcanvas')()

    def reopen(self):
        """Reopen the viewer window if the user closes it accidentally."""
        if self._server:
            self._open_browser()
        else:
            # start up a new server for the user
            self._start_server()

    def _start_server(self):
        """Start up a viewing server."""
        # Start viewer server
        # IMPORTANT: if running in an IPython/Jupyter notebook,
        # use the no_ioloop=True option
        from ginga.web.pgw import ipg
        if not self._port:
            import socket
            import errno
            socket.setdefaulttimeout(0.05)
            ports = [p for p in range(8800, 9000) if
                     socket.socket().connect_ex(('127.0.0.1', p)) not in
                     (errno.EAGAIN, errno.EWOULDBLOCK)]
            self._port = ports[0]

        self._server = ipg.make_server(host=self._host,
                                       port=self._port,
                                       use_opencv=self.use_opencv,
                                       numthreads=self._threads)

        try:
            backend_check = get_ipython().config
        except NameError:
            backend_check = {}
        no_ioloop = False  # ipython terminal
        if 'IPKernelApp' in backend_check:
            no_ioloop = True  # jupyter console and notebook

        self._server.start(no_ioloop=no_ioloop)

    def _shutdown(self):
        self._server.stop()  # stop accepting connections
        print('Stopped http server')

    def close(self):
        """Close the viewing window."""
        self._shutdown()
