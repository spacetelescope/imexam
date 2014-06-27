# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
This class supports communication with a Ginga-based viewer.

For generality, we create a matplotlib-backend simple Ginga viewer.
This kind of viewer is less performant speed-wise than if we
choose a particular widget back end.  OTOH, we don't have to
care what widget set the user has installed and the overplotting
capabilities are very, very good!

For default key and mouse shortcuts in a Ginga window, see:
    https://ginga.readthedocs.org/en/latest/quickref.html

For more information about Ginga, visit
    https://github.com/ejeschke/ginga
"""

from __future__ import print_function, division, absolute_import

import sys, os
import time
import warnings
import logging
import threading

from . import util

try:
    import astropy
except ImportError:
    raise ImportError("astropy is required")

from astropy.io import fits
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
# turn on interactive mode
plt.ion()

# Ginga imports
from ginga.mplw.ImageViewCanvasMpl import ImageViewCanvas
from ginga.mplw.ImageViewCanvasTypesMpl import DrawingCanvas
from ginga.misc import log
from ginga.AstroImage import AstroImage
from ginga import cmap
# add matplotlib colormaps to ginga's own set
cmap.add_matplotlib_cmaps()


__all__ = ['ginga_mp']


# make a new object for every window you want to create

class ginga_mp(object):

    """ A class which controls all interactions between the user and the
    ginga window

        The ginga_mp() contructor creates a new window. 

        Parameters
        ----------
        close_on_del : boolean, optional
            If True, try to close the window when this instance is deleted.


        Attributes
        ----------

        view: Ginga view object
             The object instantiated from a Ginga view class

        figure: a matplotlib figure
            (only valid if the Ginga backend is a matplotlib figure)

    """

    def __init__(self, backend='matplotlib', close_on_del=True):
        """

        Notes
        -----
        """
        self._close_on_del = close_on_del
        # dictionary where each key is a frame number, and the values are a dictionary of details
        # about the image loaded in that frame
        self._viewer = dict()
        self._current_frame = 1
        self._current_slice = None

        self.view = None  # ginga view object
        self.figure = None  # matplotlib figure
        self.backend = backend

        self._define_cmaps()  # set up possible color maps

        # for synchronizing on keystrokes
        self._cv = threading.RLock()
        self._kv = []
        self._capturing = False

        use_logger = False
        self.logger = log.get_logger(null=not use_logger, log_stderr=True)
        
        if backend == 'matplotlib':
            # create a regular matplotlib figure
            fig = plt.figure()
            self.figure = fig

            # create a ginga object, initialize some defaults and
            # tell it about the figure
            view = ImageViewCanvas(self.logger)
            view.enable_autocuts('on')
            view.set_autocut_params('zscale')
            view.set_figure(fig)

            # enable all interactive ginga features
            view.get_bindings().enable_all(True)
            self.view = view

            fig.show()

        # create a canvas that we insert when doing imexam mode
        canvas = DrawingCanvas()
        canvas.enable_draw(False)
        canvas.add_callback('key-press', self._key_press_cb)
        canvas.setSurface(self.view)
        canvas.ui_setActive(True)
        self.canvas = canvas
        

    def _capture(self):
        """
        Insert our canvas so that we intercept all events before they reach
        processing by the bindings layer of Ginga.
        """
        # insert the canvas
        self.view.onscreen_message("Moving to capture mode",
                                   delay=1.0)
        self.view.add(self.canvas, tag='mycanvas')
        self._capturing = True

    def _release(self):
        """
        Remove our canvas so that we no longer intercept events.
        """
        # retract the canvas 
        self.view.onscreen_message("Moving to regular mode",
                                   delay=1.0)
        self._capturing = False
        self.view.deleteObjectByTag('mycanvas')

    def __str__(self):
        return "<ginga viewer>"

    def __del__(self):
        if self._close_on_del:
            self.close()

    def _set_frameinfo(self, frame, fname=None, hdu=None, data=None, 
                       image=None):
        """Set the name and extension information for the data displayed in
        frame n and gather header information.

        Notes
        -----
        """

        # check the current frame, if none exists, then don't continue
        if frame:
            if frame not in self._viewer.keys():
                self._viewer[frame] = dict()

            if data == None:
                try:
                    data = self._viewer[frame]['user_array']
                except KeyError:
                    pass

            extver = None  # extension number
            extname = None  # name of extension
            filename = None  # filename of image
            numaxis = 2  # number of image planes, this is NAXIS
            naxis = (0)  # tuple of each image plane, defaulted to 1 image plane
            iscube = False  # data has more than 2 dimensions and loads in cube/slice frame
            mef_file = False  # used to check misleading headers in fits files

            if hdu:
                pass
                ## naxis.reverse()  # for astropy.fits row-major ordering
                ## naxis = map(int, naxis)
                ## naxis = [axis - 1 if axis > 0 else 0 for axis in naxis]  # zero index fits
                ## naxis = tuple(naxis)

                ## # set the extension from the header information returned from DS9
                ## # this is the best way to get the information if the user changes
                ## # the loaded file using the gui
                ## header_cards = fits.Header.fromstring(self.get_header(), sep='\n')
                ## mef_file = self._check_filetype(filename)
                ## if mef_file:
                ##     try:
                ##         extver = int(header_cards['EXTVER'])
                ##     except KeyError:
                ##         extver = 1  # fits doesn't require extver if there is only 1 extension

                ##     try:
                ##         extname = str(header_cards['EXTNAME'])
                ##     except KeyError:
                ##         extname = None

                ## try:
                ##     numaxis = int(header_cards['NAXIS'])
                ## except KeyError:
                ##     raise KeyError("Problem getting NAXIS from header")

                ## if not iscube:
                ##     if numaxis > 2:
                ##         iscube = True
                ##         naxis = list()
                ##         # assume the first axis in each extension is displayed
                ##         for axis in range(numaxis, 2, -1):
                ##             naxis.append(0)
                ##         naxis = tuple(naxis)

            # update the viewer dictionary, if the user changes what's displayed in a frame this should update correctly
            # this dictionary will be referenced in the other parts of the code. This enables tracking user arrays through
            # frame changes

            self._viewer[frame] = {'filename': fname,
                                   'extver': extver,
                                   'extname': extname,
                                   'naxis': naxis,
                                   'numaxis': numaxis,
                                   'iscube':  iscube,
                                   'user_array': data,
                                   'image': image,
                                   'hdu': hdu,
                                   'mef': mef_file}

    def _check_filetype(self, filename=None):
        """check the file to see if the file is a multi-extension fits file"""
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

    def valid_data_in_viewer(self):
        """return bool if valid file or array is loaded into the viewer"""
        frame = self.frame()

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
            except AttributeError, ValueError:
                valid = False
                print("error in array")

            return valid

    def get_filename(self):
        """return the filename currently on display"""
        frame = self.frame()
        if frame:
            return self._viewer[frame]['filename']

    def get_frame_info(self):
        """return more explicit information about the data displayed in the current frame"""
        return self._viewer[self.frame()]

    def get_viewer_info(self):
        """Return a dictionary of information about all frames which are loaded with data"""
        return self._viewer

    def close(self):
        """ close the window"""
        self.figure.close()

    def readcursor(self):
        """returns image coordinate postion and key pressed, 

        Notes
        -----
        """
        # insert canvas to trap keyboard events if not already inserted
        if not self._capturing:
            self._capture()

        with self._cv:
            self._kv = ()
            
        # wait for an event
        # it would be better to program this using events driven
        # by keystrokes, but the caller is using a procedural style
        while True:
            # ugly hack to suppress deprecation warning by mpl
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # run event loop, so window can get a keystroke
                self.figure.canvas.start_event_loop(timeout=0.1)

            with self._cv:
                # did we get a key event?
                if len(self._kv) > 0:
                    (k, x, y) = self._kv
                    break

        # ginga is returning 0 based indexes
        return x+1, y+1, k

    def _define_cmaps(self):
        """setup the default color maps which are available"""

        # get ginga color maps
        self._cmap_colors = cmap.get_names()

    def cmap(self, color=None, load=None, invert=False, save=False, filename='colormap.ds9'):
        """ Set the color map table to something else, using a defined list of options  


        Parameters
        ----------
        color: string
            color must be set to one of the available DS9 color map names

        load: string, optional
            set to the filename which is a valid colormap lookup table
            valid contrast values are from 0 to 10, and valid bias values are from 0 to 1

        invert: bool, optional
            invert the colormap

        save: bool, optional
            save the current colormap as a file   

        filename: string, optional
            the name of the file to save the colormap to

        """

        if color:
            if color in self._cmap_colors:
                self.view.set_color_map(color)
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


    def frame(self, n=None):
        """convenience function to change or report frames


        Parameters
        ----------
        n: int, string, optional
            The frame number to open or change to. If the number specified doesn't exist, a new frame will be opened
            If nothing is specified, then the current frame number will be returned. 

        Examples
        --------
        frame(1)  sets the current frame to 1
        frame("last") set the current frame to the last frame
        frame() returns the number of the current frame
        frame("new") opens a new frame
        frame(3)  opens frame 3 if it doesn't exist already, otherwise goes to frame 3

        """
        frame = self._current_frame
        n_str = str(n)
        frames = self._viewer.keys()
        frames.sort()

        if not n is None:
            if n_str == "delete":
                if frame in frames:
                    del self._viewer[frame]
                    frames = self._viewer.keys()
                    if len(frames) > 0:
                        n = frames[0]
                    else:
                        n = None
                        
            elif n_str == "new":
                n = frames[-1]
                n += 1
                self._set_frameinfo(n)
                
            elif n_str == "last":
                n = frames[-1]

            elif n_str == "first":
                n = frames[0]
                
            else:
                n = int(n)
                if not n in frames:
                    print("%d is not a created frame." % (n))
                        
            self._current_frame = n
            image = self._viewer[frame]['image']
            if image != None:
                self.view.set_image(image)
            return n

        else:
            return frame

    def iscube(self):
        """return information on whether a cube image is displayed in the current frame"""
        frame = self.frame()
        if frame:
            return self._viewer[frame]['iscube']

    def get_slice_info(self):
        """return the slice tuple that is currently displayed"""
        frame = self.frame()

        if self._viewer[frame]['iscube']:
            image_slice = self._viewer[frame]['naxis']
        else:
            image_slice = None
        return image_slice

    def get_data(self):
        """ return a numpy array of the data displayed in the current frame

        Notes
        -----
        """

        frame = self.frame()
        if frame:
            if isinstance(self._viewer[frame]['user_array'], np.ndarray):
                return self._viewer[frame]['user_array']

            elif self._viewer[frame]['hdu'] != None:
                return self._viewer[frame]['hdu'].data

            elif self._viewer[frame]['image'] != None:
                return self._viewer[frame]['image'].get_data()


    def get_header(self):
        """return the current fits header as a string or None if there's a problem"""

        # TODO return the simple header for arrays which are loaded

        frame = self.frame()
        if frame and self._viewer[frame]['hdu'] != None:
            hdu = self._viewer[frame]['hdu']
            return hdu.header
        else:
            warnings.warn("No file with header loaded into ginga")
            return None

    def _key_press_cb(self, canvas, keyname):
        if keyname == 'q':
            self._release()
        
        data_x, data_y = self.view.get_last_data_xy()
        ## print("key %s pressed at data %f,%f" % (
        ##     keyname, data_x, data_y))
        with self._cv:
            self._kv = (keyname, data_x, data_y)
        return True

    def load_fits(self, fname="", extver=1, extname=None):
        """convenience function to load fits image to current frame

        Parameters
        ----------
        fname: string, optional
            The name of the file to be loaded. You can specify the full extension in the name, such as
            filename_flt.fits[sci,1] or filename_flt.fits[1]

        extver: int, optional
            The extension to load (EXTVER in the header)

        extname: string, optional
            The name (EXTNAME in the header) of the image to load

        Notes
        -----
        """
        if fname:
            # see if the image is MEF or Simple
            fname = os.path.abspath(fname)
            try:
                #mef_file = self._check_filetype(shortname)
                image = AstroImage()
                with fits.open(fname) as filedata:
                    hdu = filedata[extver - 1]
                    image.load_hdu(hdu)
                    
            except Exception as e:
                print("Exception: {0}".format(e))
                raise IOError

            frame = self.frame()
            self._set_frameinfo(frame, fname=fname, hdu=hdu, image=image)
            self.view.set_image(image)

        else:
            print("No filename provided")

    def panto_image(self, x, y):
        """convenience function to change to x,y  physical image coordinates


        Parameters
        ----------
        x: float
            X location in physical coords to pan to

        y: float
            Y location in physical coords to pan to


        """
        # ginga deals in 0-based coords
        x, y = x - 1, y - 1
        
        self.view.set_pan(x, y)

    def panto_wcs(self, x, y, system='fk5'):
        """pan to wcs location coordinates in image


        Parameters
        ----------

        x: string
            The x location to move to, specified using the given system
        y: string
            The y location to move to
        system: string
            The reference system that x and y were specified in, they should be understood by DS9        

        """
        # this should be replaced by querying our own copy of the wcs
        image = self.view.get_image()
        a, b = image.radectopix(x, y, coords='data')
        self.view.set_pan(a, b)

    def rotate(self, value=None):
        """rotate the current frame (in degrees), the current rotation is printed with no params

        Parameters
        ----------

        value: float [degrees]
            Rotate the current frame {value} degrees
            If value is None, then the current rotation is printed

        """
        if value is not None:
            self.view.rotate(value)

        rot_deg = self.view.get_rotation()
        print("Image rotated at {0:f} deg".format(rot_deg))

    def transform(self, flipx=None, flipy=None, flipxy=None):
        """transform the frame

        Parameters
        ----------

        flipx: boolean
            if True flip the X axis, if False don't, if None leave current
        flipy: boolean
            if True flip the Y axis, if False don't, if None leave current
        swapxy: boolean
            if True swap the X and Y axes, if False don't, if None leave current
        """
        _flipx, _flipy, _swapxy = self.view.get_transform()

        # preserve current transform if not supplied as a parameter
        if flipx is None:
            flipx = _flipx
        if flipy is None:
            flipy = _flipy
        if swapxy is None:
            swapxy = _swapxy
            
        self.view.transform(flipx, flipy, swapxy)

    def save_png(self, filename=None):
        """save a frame display as a PNG file

        Parameters
        ----------

        filename: string
            The name of the output PNG image

        """
        if not filename:
            print("No filename specified, try again")
        else:
            buf = self.view.get_png_image_as_buffer()
            with open(filename, 'w') as out_f:
                out_f.write(buf)

    def scale(self, scale='zscale'):
        """ The default zscale is the most widely used option

        Parameters
        ----------

        scale: string
            The scale for ds9 to use, these are set strings of 
            [linear|log|pow|sqrt|squared|asinh|sinh|histequ]

        Notes
        -----
        """

        # setting the autocut method?
        mode_scale = self.view.get_autocut_methods()

        if scale in mode_scale:
            self.view.set_autocut_params(scale)
            return

        # setting the color distribution algorithm?
        color_dist = self.view.get_color_algorithms()

        if scale in color_dist:
            self.view.set_color_algorithm(scale)
            return

    def view(self, img):
        """ Display numpy image array to current frame

        Parameters
        ----------
        img: numpy array
            The array containing data, it will be forced to numpy.array()

        """

        frame = self.frame()
        if not frame:
            print("No valid frame")
        else:
            img_np = np.array(img)
            image = AstroImage(img_np, logger=self.logger)
            self._set_frameinfo(frame, data=img_np, image=image)
            self.view.set_image(image)

    def zoomtofit(self):
        """convenience function for zoom"""
        self.view.zoom_fit()

    def zoom(self, zoomlevel):
        """ zoom using the specified level

        Parameters
        ----------
        zoomlevel: integer

        Examples
        --------
        zoom(6)
        zoom(-3)

        """

        try:
            self.view.zoom_to(zoomlevel)
            
        except Exception as e:
            print("problem with zoom: %s" % str(e))


