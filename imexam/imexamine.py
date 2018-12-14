"""Licensed under a 3-clause BSD style license - see LICENSE.rst.

   This class implements IRAF/imexamine type capabilities
   for providing powerful diagnostic quick-look tools.

   However, the power of this python tool is that it is essentially a library
   of plotting and analysis routines which can be directed towards
   any viewer. It can also be used without connecting to any viewer
   since the calls take only data,x,y information. This means that
   given a data array and a list of x,y positions you can creates
   plots without havin to interact with the viewers.

   Users can also register a custom function with the class
   and have it available for use in either case.

   The plots which are made are fully customizable

 """

from __future__ import print_function, division, absolute_import

import matplotlib.pyplot as plt
# turn on interactive mode for plotting
# so that plt.show becomes non-blocking
if not plt.isinteractive():
    plt.ion()

import warnings
import numpy as np
import sys
import logging
import tempfile
from copy import deepcopy


from matplotlib import get_backend

from astropy.io import fits
from astropy.modeling import models
from astropy.visualization import ZScaleInterval

try:
    from scipy import stats
    scipy_installed = True
except ImportError:
    scipy_installed = False
    print("Scipy not installed, describe stat unavailable")

from . import math_helper
from . import imexam_defpars
from .util import set_logging

if sys.version_info.major < 3:
    PY3 = False
else:
    PY3 = True

# enable display plot in iPython notebook
try:
    from io import StringIO
except ImportError:
    from cString import StringIO

try:
    import photutils
    photutils_installed = True
except ImportError:
    print("photutils not installed, photometry functionality "
          "in imexam() not available")
    photutils_installed = False

__all__ = ["Imexamine"]


class Imexamine(object):
    """The imexamine class controls plotting and analysis functions."""

    def __init__(self):
        """do imexamine like routines on the current frame.

        read the returned cursor key value to decide what to do

        region_size is the default radius or side of the square for stat info
        """
        self.set_option_funcs()  # define the dictionary of keys and functions
        self._data = np.zeros(0)  # the data array
        self._datafile = ""  # the file from which the data came
        # read from imexam_defpars which contains dicts
        self._define_default_pars()
        # default plot name saved with "s" key
        self.plot_name = "imexam_plot.pdf"
        # let users have multiple plot windows, the list stores their names
        self._plot_windows = list()
        # this contains the name of the current plotting window
        self._figure_name = "imexam"
        self._plot_windows.append(self._figure_name)
        self._reserved_keys = ['q', '2']  # not to be changed with user funcs
        self._fit_models = ["Gaussian1D",
                            "Moffat1D",
                            "MexicanHat1D",
                            "AiryDisk2D",
                            "Polynomial1D"]

        # see if the package logger was already started
        self.log = logging.getLogger(__name__)
        self.log = set_logging()

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
            self.log = set_logging(filename, on, level)

    def _close_plots(self):
        """Make sure to release plot memory at end of exam loop."""
        for plot in self._plot_windows:
            plt.close()

    def close(self):
        """For use with the Imexamine object standalone."""
        self._close_plots()
        self.log = set_logging(on=False)

    def show_fit_models(self):
        """Print the available astropy models for plot fits."""
        self.log.info("The available astropy models for fitting"
                      "are: {}".format(self._fit_models))

    def set_option_funcs(self):
        """Define the dictionary which maps imexam keys to their functions.

         Notes
         -----
         The user can modify this dictionary to add or change options,
         the first item in the tuple is the associated function
         the second item in the tuple is the description of what the function
         does when that key is pressed
        """
        self.imexam_option_funcs = {'a': (self.aper_phot, 'Aperture sum, with radius region_size '),
                                    'j': (self.line_fit, '1D [Gaussian1D default] line fit '),
                                    'k': (self.column_fit, '1D [Gaussian1D default] column fit'),
                                    'm': (self.report_stat, 'Square region stats, in [region_size],default is median'),
                                    'x': (self.show_xy_coords, 'Return x,y,value of pixel'),
                                    'y': (self.show_xy_coords, 'Return x,y,value of pixel'),
                                    'l': (self.plot_line, 'Return line plot'),
                                    'c': (self.plot_column, 'Return column plot'),
                                    'g': (self.curve_of_growth, 'Return curve of growth plot'),
                                    'r': (self.radial_profile, 'Return the radial profile plot'),
                                    'h': (self.histogram, 'Return a histogram in the region around the cursor'),
                                    'e': (self.contour, 'Return a contour plot in a region around the cursor'),
                                    's': (self.save_figure, 'Save current figure to disk as [plot_name]'),
                                    'b': (self.gauss_center, 'Return the 2D gauss fit center of the object'),
                                    'w': (self.surface, 'Display a surface plot around the cursor location'),
                                    '2': (self.new_plot_window, 'Make the next plot in a new window'),
                                    't': (self.cutout, 'Make a fits image cutout using pointer location')
                                    }

    def print_options(self):
        """Print the imexam options to screen."""
        keys = self.get_options()
        for key in keys:
            print("%s\t%s" % (key, self.option_descrip(key)))

    def do_option(self, x, y, key):
        """Run the imexam option.

        Parameters
        ----------

        x: int
            The x location of the cursor or data point

        y: int
            The y location of the cursor or data point

        key: string
            The key which was pressed

        """
        self.log.debug("pressed: {0}, {1:s}".format(key, self.imexam_option_funcs[key][0].__name__))
        self.imexam_option_funcs[key][0](x, y, self._data)

    def get_options(self):
        """Return the imexam options as a key list."""
        keys = sorted(self.imexam_option_funcs.keys())
        return keys

    def option_descrip(self, key, field=1):
        """Return the looked up dictionary of options.

        Parameters
        ----------
        key: string
            The key which was pressed, it relates to the function to call

        field: int
            This tells where in the option dictionary the function name
            can be found
        """
        return self.imexam_option_funcs[key][field]

    def set_data(self, data=np.zeros(0)):
        """initialize the data that imexamine uses."""
        self._data = data

    def set_plot_name(self, filename=None):
        """set the default plot name for the "s" key.

        Parameters
        ----------
        filename: string
          The name which is used to save the current plotting window to a file
          The extension on the name decides which file type is used
        """
        if filename is None:
            warnings.warn("No filename provided")
        else:
            self.plot_name = filename

    def get_plot_name(self):
        """return the default plot name."""
        return self.plot_name

    def _define_default_pars(self):
        """Set all pars to their defaults, stored in a file with dicts."""
        self.aper_phot_def_pars = imexam_defpars.aper_phot_pars
        self.radial_profile_def_pars = imexam_defpars.radial_profile_pars
        self.curve_of_growth_def_pars = imexam_defpars.curve_of_growth_pars
        self.surface_def_pars = imexam_defpars.surface_pars
        self.line_fit_def_pars = imexam_defpars.line_fit_pars
        self.column_fit_def_pars = imexam_defpars.column_fit_pars
        self.contour_def_pars = imexam_defpars.contour_pars
        self.histogram_def_pars = imexam_defpars.histogram_pars
        self.lineplot_def_pars = imexam_defpars.lineplot_pars
        self.colplot_def_pars = imexam_defpars.colplot_pars
        self.histogram_def_pars = imexam_defpars.histogram_pars
        self.contour_def_pars = imexam_defpars.contour_pars
        self.report_stat_def_pars = imexam_defpars.report_stat_pars
        self.cutout_def_pars = imexam_defpars.cutout_pars
        self._define_local_pars()

    def _define_local_pars(self):
        """Set a copy of the default pars that users can alter."""
        self.aper_phot_pars = deepcopy(self.aper_phot_def_pars)
        self.radial_profile_pars = deepcopy(self.radial_profile_def_pars)
        self.curve_of_growth_pars = deepcopy(self.curve_of_growth_def_pars)
        self.surface_pars = deepcopy(self.surface_def_pars)
        self.line_fit_pars = deepcopy(self.line_fit_def_pars)
        self.column_fit_pars = deepcopy(self.column_fit_def_pars)
        self.contour_pars = deepcopy(self.contour_def_pars)
        self.histogram_pars = deepcopy(self.histogram_def_pars)
        self.lineplot_pars = deepcopy(self.lineplot_def_pars)
        self.colplot_pars = deepcopy(self.colplot_def_pars)
        self.histogram_pars = deepcopy(self.histogram_def_pars)
        self.contour_pars = deepcopy(self.contour_def_pars)
        self.report_stat_pars = deepcopy(self.report_stat_def_pars)
        self.cutout_pars = deepcopy(self.cutout_def_pars)

    def unlearn_all(self):
        """reset the default parameters for all functions."""
        self._define_local_pars()

    def new_plot_window(self, x, y, data=None):
        """make the next plot in a new plot window.

        Notes
        -----
        x,y, data, are not used here, but the calls are setup to take them
        for all imexam options. Is there a better way to do the calls in
        general? Once the new plotting window is open all plots will be
        directed towards it. The old window cannot be used again.

        """
        if data is None:
            data = self._data
        self._figure_name = "imexam" + str(len(self._plot_windows) + 1)
        self._plot_windows.append(self._figure_name)
        self.log.info("Plots now directed towards {0:s}".format(self._figure_name))

    def plot_line(self, x, y, data=None, fig=None):
        """line plot of data at point x.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        fig: figure object for redirect
            Used for interaction with the ginga GUI
        """
        if data is None:
            data = self._data
        self.log.info("Line at {0} {1}".format(x, y))

        pfig = fig
        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca()

        if self.lineplot_pars["title"][0] is None:
            ax.set_title("{0:s} line at {1:d}".format(self._datafile, int(y)))
        ax.set_xlabel(self.lineplot_pars["xlabel"][0])
        ax.set_ylabel(self.lineplot_pars["ylabel"][0])

        if not self.lineplot_pars["xmax"][0]:
            xmax = len(data[int(y), :])
        else:
            xmax = self.lineplot_pars["xmax"][0]
        ax.set_xlim(self.lineplot_pars["xmin"][0], xmax)

        if self.lineplot_pars["logx"][0]:
            ax.set_xscale("log")
        if self.lineplot_pars["logy"][0]:
            ax.set_yscale("log")

        if bool(self.lineplot_pars["pointmode"][0]):
            ax.plot(data[int(y), :], self.lineplot_pars["marker"][0])
        else:
            ax.plot(data[int(y), :])

        if pfig is None and 'nbagg' not in get_backend().lower():
            plt.draw()
            plt.pause(0.001)
        else:
            fig.canvas.draw()

    def plot_column(self, x, y, data=None, fig=None):
        """column plot of data at point y.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        fig: figure name for redirect
            Used for interaction with the ginga GUI
        """
        if data is None:
            data = self._data
        self.log.info("Column at {0} {1}".format(x, y))

        pfig = fig
        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca()

        if self.colplot_pars["title"][0] is None:
            ax.set_title("{0:s} column at {1:d}".format(self._datafile, int(x)))
        else:
            ax.set_title(self.colplot_pars["title"][0])
        ax.set_xlabel(self.colplot_pars["xlabel"][0])
        ax.set_ylabel(self.colplot_pars["ylabel"][0])

        if not self.colplot_pars["xmax"][0]:
            xmax = len(data[:, int(x)])
        else:
            xmax = self.colplot_pars["xmax"][0]
        ax.set_xlim(self.colplot_pars["xmin"][0], xmax)

        if self.colplot_pars["logx"][0]:
            ax.set_xscale("log")

        if self.colplot_pars["logy"][0]:
            ax.set_yscale("log")
        if bool(self.colplot_pars["pointmode"][0]):
            ax.plot(data[:, int(x)], self.colplot_pars["marker"][0])
        else:
            ax.plot(data[:, int(x)])

        if pfig is None and 'nbagg' not in get_backend().lower():
            plt.draw()
            plt.pause(0.001)
        else:
            fig.canvas.draw()

    def show_xy_coords(self, x, y, data=None):
        """print the x,y,value to the screen.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        """
        if data is None:
            data = self._data
        info = "{0} {1}  {2}".format(x, y, data[int(y), int(x)])
        self.log.info(info)

    def report_stat(self, x, y, data=None):
        """report the statisic of values in a box with side region_size.

        The statistic can be any numpy function

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        """
        if data is None:
            data = self._data

        region_size = self.report_stat_pars["region_size"][0]
        name = self.report_stat_pars["stat"][0]
        dist = region_size / 2
        xmin = int(x - dist)
        xmax = int(x + dist)
        ymin = int(y - dist)
        ymax = int(y + dist)

        if (("describe" in name) and (scipy_installed)):
            try:
                stat = getattr(stats, "describe")
                nobs, minmax, mean, var, skew, kurt = stat(data[ymin:ymax,
                                                           xmin:xmax].flatten())
                pstr = ("[{0:d}:{1:d},{2:d}:{3:d}] {4:s}: \nnobs: "
                        "{5}\nminmax: {6}\nmean {7}\nvariance: {8}\nskew: "
                        "{9}\nkurtosis: {10}".format(ymin, ymax, xmin, xmax,
                                                     name, nobs, minmax, mean,
                                                     var, skew, kurt))
            except AttributeError:
                warnings.warn("Invalid stat specified")
        else:
            try:
                stat = getattr(np, name)
                pstr = "[{0:d}:{1:d},{2:d}:{3:d}] {4:s}: {5}".format(
                       ymin, ymax, xmin, xmax, name,
                       (stat(data[ymin:ymax, xmin:xmax])))
            except AttributeError:
                warnings.warn("Invalid stat specified")

        self.log.info(pstr)

    def save_figure(self, x, y, data=None, fig=None):
        """Save to file the figure that's currently displayed.

        this is used for the imexam loop, because there is a standard api
        for the loop

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        fig: figure for redirect
            Used for interaction with the ginga GUI
        """
        if data is None:
            data = self._data
        if fig is None:
            fig = plt.figure(self._figure_name)
        ax = fig.gca()
        fig.savefig(self.plot_name)
        pstr = "plot saved to {0:s}".format(self.plot_name)
        self.log.info(pstr)

    def save(self, filename=None, fig=None):
        """Save to file the figure that's currently displayed.

        this is used for the standalone plotting

        Parameters
        ----------
        filename: string
            Name of the file the plot will be saved to. The extension
            on the filename determines the filetype
        fig: figure name for redirect
            Used for interaction with the ginga GUI
        """
        if filename:
            self.set_plot_name(filename)
        else:
            self.set_plot_name(self._figure_name + ".pdf")

        if fig is None:
            fig = plt.figure(self._figure_name)
        ax = fig.gca()
        fig.savefig(self.plot_name)
        pstr = "plot saved to {0:s}".format(self.plot_name)
        self.log.info(pstr)

    def aper_phot(self, x, y, data=None, fig=None):
        """Perform aperture photometry.

        uses photutils functions, photutils must be available

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        fig: figure object for redirect
            Used for interaction with the ginga GUI
        """
        if data is None:
            data = self._data

        center = False
        if not photutils_installed:
            self.log.warning("Install photutils to enable")
        else:
            if self.aper_phot_pars["center"][0]:
                center = True
                delta = 10
                amp, x, y, sigma, sigmay = self.gauss_center(x, y, data,
                                                             delta=delta)

            # XXX TODO:  Do I beleive that these all have to be ints?
            radius = int(self.aper_phot_pars["radius"][0])
            width = int(self.aper_phot_pars["width"][0])
            inner = int(self.aper_phot_pars["skyrad"][0])
            subsky = bool(self.aper_phot_pars["subsky"][0])

            outer = inner + width

            apertures = photutils.CircularAperture((x, y), radius)
            rawflux_table = photutils.aperture_photometry(
                data,
                apertures,
                subpixels=1,
                method="center")

            sky_per_pix = None
            if subsky:
                annulus_apertures = photutils.CircularAnnulus(
                    (x, y), r_in=inner, r_out=outer)
                bkgflux_table = photutils.aperture_photometry(
                    data,
                    annulus_apertures)

                # to calculate the mean local background, divide the circular
                # annulus aperture sums by the area fo the circular annulus.
                # The bkg sum with the circular aperture is then
                # then mean local background tims the circular apreture area.
                aperture_area = apertures.area()
                annulus_area = annulus_apertures.area()

                bkg_sum = float(
                    (bkgflux_table['aperture_sum'] *
                     aperture_area /
                     annulus_area)[0])
                total_flux = rawflux_table['aperture_sum'][0] - bkg_sum
                sky_per_pix = float(
                    bkgflux_table['aperture_sum'] /
                    annulus_area)

            else:
                total_flux = float(rawflux_table['aperture_sum'][0])

            # compute the magnitude of the sky corrected flux
            magzero = float(self.aper_phot_pars["zmag"][0])
            mag = magzero - 2.5 * (np.log10(total_flux))

            # Construct the output strings (header and parameter values)
            pheader = "x\ty\tradius\tflux\tmag(zpt={0:0.2f})\t".format(magzero)
            pstr = "\n{0:.2f}\t{1:0.2f}\t{2:d}\t{3:0.2f}\t{4:0.2f}\t".format(x,
                                                                             y,
                                                                             radius,
                                                                             total_flux,
                                                                             mag)

            if sky_per_pix is not None:
                pheader += "sky/pix\t"
                pstr += "{0:0.2f}\t".format(sky_per_pix)
            if center:
                pheader += "fwhm(pix)"
                pstr += "{0:0.2f}".format(math_helper.gfwhm(sigma)[0])

            pheader = pheader.expandtabs(15)
            pstr = pstr.expandtabs(15)

            # Save the total flux for unit testing things later
            self.total_flux = total_flux

            self.log.info(pheader + pstr)
            if self.aper_phot_pars["genplot"][0]:
                pfig = fig
                if fig is None:
                    # Make sure figure is square so round stars look round
                    fig = plt.figure(self._figure_name, figsize=[5, 5])
                fig.clf()
                fig.add_subplot(111)
                ax = plt.gca()

                if self.aper_phot_pars["title"][0] is None:
                    title = "x=%.2f, y=%.2f, flux=%.1f, \nmag=%.1f, sky=%.1f" %(x, y,
                                                                                total_flux, mag,
                                                                                sky_per_pix)
                    if center:
                        title += ", fwhm=%.2f" % math_helper.gfwhm(sigma)[0]
                    ax.set_title(title)
                else:
                    ax.set_title(self.aper_phot_pars["title"][0])

                if self.aper_phot_pars['scale'][0] == 'zscale':
                    zs = ZScaleInterval()
                    color_range = zs.get_limits(data)
                else:
                    color_range = [self.aper_phot_pars['color_min'][0],
                                   self.aper_phot_pars['color_max'][0]]

                pad = outer * 1.2  # XXX TODO: Bad magic number
                ax.imshow(data[int(y - pad):int(y + pad),
                               int(x - pad):int(x + pad)],
                          vmin=color_range[0], vmax=color_range[1],
                          extent=[int(x - pad), int(x + pad),
                                  int(y - pad), int(y + pad)], origin='lower',
                          cmap=self.aper_phot_pars['cmap'][0])

                apertures.plot(ax=ax, color='green', alpha=0.75, lw=3)
                if subsky:
                    annulus_apertures.plot(ax=ax, color='red', alpha=0.75, lw=3)

                if pfig is None and 'nbagg' not in get_backend().lower():
                    plt.draw()
                    plt.pause(0.001)
                else:
                    fig.canvas.draw()

    def line_fit(self, x, y, data=None, form=None, genplot=True, fig=None, col=False):
        """compute the 1D fit to the line of data using the specified form.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        form: string
            This is the functional form specified in the line fit parameters
            see show_fit_models()
        genplot: bool
            produce the plot or return the fit
        fig: figure for redirect
            Used for interaction with the ginga GUI
        col: bool (False)
            Plot column instead of line

        Notes
        -----
        The background is currently ignored

        If centering is True in the parameter set, then the center
        is fit with a 2d gaussian, not performed for Polynomial1D
        """

        # Set which parameters to use
        if col:
            pars = self.column_fit_pars
        else:
            pars = self.line_fit_pars

        if data is None:
            data = self._data

        if form is None:
            fitform = getattr(models, pars["func"][0])
        else:
            if form in self._fit_models:
                fitform = getattr(models, form)
            else:
                raise ValueError("Functional form not in available: {}"
                                 .format(self._fit_models))

        self.log.info("using model: {0}".format(fitform))

        # Used for Polynomial1D fitting
        degree = int(pars["order"][0])

        delta = int(pars["rplot"][0])
        if delta >= len(data) / 4:  # help with small data arrays and defaults
            delta = delta / 2
        delta = int(delta)

        xx = int(x)
        yy = int(y)

        # fit the center with a 2d gaussian
        if pars["center"][0]:
            if fitform.name is not "Polynomial1D":
                amp, xout, yout, sigma, sigmay = self.gauss_center(xx,
                                                                   yy,
                                                                   data,
                                                                   delta=delta)
                if (xout < 0 or yout < 0 or xout > data.shape[1] or
                   yout > data.shape[0]):
                        self.log.warning("Problem with centering, "
                                         "pixel coords")
                else:
                    xx = int(xout)
                    yy = int(yout)
        if col:
            line = data[:, xx]
            chunk = line[yy - delta:yy + delta]
            delta_add = yy - delta
        else:
            line = data[yy, :]
            chunk = line[xx - delta: xx + delta]
            delta_add = xx - delta

        # This factor is passed to the fitter
        if pars["clip"][0]:
            sig_factor = pars["sigma"][0]
        else:
            sig_factor = 0

        # fit model to data
        if fitform.name is "Gaussian1D":
            xr = np.arange(len(chunk))
            fitted = math_helper.fit_gauss_1d(xr, chunk, sigma_factor=sig_factor)
            fitted.mean_0.value += delta_add
        elif fitform.name is "Moffat1D":
            fitted = math_helper.fit_moffat_1d(chunk, sigma_factor=sig_factor)
            fitted.x_0_0.value += delta_add
        elif fitform.name is "MexicanHat1D":
            fitted = math_helper.fit_mex_hat_1d(chunk, sigma_factor=sig_factor)
            fitted.x_0_0.value += delta_add
        elif fitform.name is "Polynomial1D":
            fitted = math_helper.fit_poly_n(chunk, deg=degree, sigma_factor=sig_factor)
            if fitted is None:
                raise ValueError("Problem with the Poly1D fit")
        elif fitform.name is "AiryDisk2D":
            fitted = math_helper.fit_airy_2d(chunk, sigma_factor=sig_factor)
            if fitted is None:
                raise ValueError("Problem with the AiryDisk2D fit")
            fitted.x_0_0.value += (xx - delta)
            fitted.y_0_0.value += (yy - delta)

        xline = np.arange(len(chunk)) + delta_add
        fline = np.linspace(xline[0], xline[-1], 100)  # finer sample

        if fitform.name is "AiryDisk2D":
            yfit = fitted(fline, fline * 0 + fitted.y_0_0.value)
        else:
            yfit = fitted(fline)

        # make a plot
        if pars["title"][0] is None:
            title = "{0}: {1} {2}".format(self._datafile, int(x), int(y))
        else:
            title = pars["title"][0]

        if genplot:
            pfig = fig
            if fig is None:
                fig = plt.figure(self._figure_name)
            fig.clf()
            fig.add_subplot(111)
            ax = fig.gca()

            ax.set_xlabel(pars["xlabel"][0])
            ax.set_ylabel(pars["ylabel"][0])
            if pars["logx"][0]:
                ax.set_xscale("log")
            if pars["logy"][0]:
                ax.set_yscale("log")

            if bool(pars["pointmode"][0]):
                ax.plot(xline, chunk, 'o', label="data")
            else:
                ax.plot(xline, chunk, label="data", linestyle='-')

            if fitform.name is "Gaussian1D":
                fwhmx, fwhmy = math_helper.gfwhm(fitted.stddev_0.value)
                ax.set_title("{0:s} amp={1:8.2f} mean={2:9.2f},"
                             "fwhm={3:9.2f}".format(title,
                                                    fitted.amplitude_0.value,
                                                    fitted.mean_0.value,
                                                    fwhmx))
                pstr = "({0:d},{1:d}) mean={2:9.2f}, fwhm={3:9.2f}".format(
                    int(x), int(y), fitted.mean_0.value, fwhmx)
                self.log.info(pstr)
            elif fitform.name is "Moffat1D":
                mfwhm = math_helper.mfwhm(fitted.alpha_0.value,
                                          fitted.gamma_0.value)
                ax.set_title("{0:s} amp={1:8.2f} fwhm={2:9.2f}".format(
                    title, fitted.amplitude_0.value, mfwhm))
                pstr = "({0:d},{1:d}) amp={2:8.2f} fwhm={3:9.2f}".format(
                    int(x), int(y), fitted.amplitude_0.value, mfwhm)
                self.log.info(pstr)
            elif fitform.name is "MexicanHat1D":
                ax.set_title("{0:s} amp={1:8.2f} sigma={2:8.2f}".format(
                    title, fitted.amplitude_0.value, fitted.sigma_0.value))
                pstr = "({0:d},{1:d}) amp={2:8.2f} sigma={3:9.2f}".format(
                    int(x), int(y), fitted.amplitude_0.value, fitted.sigma_0.value)
                self.log.info(pstr)
            elif fitform.name is "Polynomial1D":
                ax.set_title("{0:s} degree={1:d}".format(title, degree))
                pstr = "({0:d},{1:d}) degree={2:d}".format(int(x), int(y), degree)
                self.log.info(fitted.parameters)
                self.log.info(pstr)
            elif fitform.name is "AiryDisk2D":
                ax.set_title("{0:s} amp={1:8.2f} radius={2:8.2f}".format(
                    title, fitted.amplitude_0.value, fitted.radius_0.value))
                pstr = "({0:d},{1:d}) amp={2:8.2f} radius={3:9.2f}".format(
                    int(x), int(y), fitted.amplitude_0.value, fitted.radius_0.value)
                self.log.info(pstr)
            else:
                warnings.warn("Unsupported functional form specified for fit")
                raise ValueError
            ax.plot(fline, yfit, c='r', label=str(fitform.__name__) + " fit")
            ax.legend()

            if pfig is None and 'nbagg' not in get_backend().lower():
                plt.draw()
                plt.pause(0.001)
            else:
                fig.canvas.draw()

        else:
            return fitted

    def column_fit(self, x, y, data=None, form=None, genplot=True, fig=None):
        """Compute the 1d fit to the column of data.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        form: string
            This is the functional form specified in the column fit parameters
        genplot: int
            produce the plot or return the fit model
        fig: figure name for redirect
            Used for interaction with the ginga GUI

        Notes
        -----
        delta is the range of data values to use around the x,y location

        The background is currently ignored

        if centering is True, then the center is fit with a 2d gaussian,
        but this is currently not done for Polynomial1D
        """

        result = self.line_fit(x, y, data=data, form=form,
                               genplot=genplot, fig=fig, col=True)
        if not genplot:
            return result

    def gauss_center(self, x, y, data=None, delta=10, sigma_factor=0):
        """Return the 2d gaussian fit center of the data.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        delta: int
            The range of data values (bounding box) to use around the x,y
            location for calculating the center
        sigma_factor: float, optional
            The sigma clipping factor to use on the data fit

        """
        if data is None:
            data = self._data

        # reset delta for small arrays
        if delta >= len(data) / 4:
            delta = delta / 2

        delta = int(delta)
        xx = int(x)
        yy = int(y)

        #  flipped from xpa
        chunk = data[yy - delta:yy + delta, xx - delta:xx + delta]
        try:
            fit = math_helper.fit_gaussian_2d(chunk, sigma_factor=sigma_factor)
            amp = fit.amplitude_0.value
            xcenter = fit.x_mean_0.value
            ycenter = fit.y_mean_0.value
            xsigma = fit.x_stddev_0.value
            ysigma = fit.y_stddev_0.value

            pstr = "xc={0:4f}\tyc={1:4f}".format(
                (xcenter + xx - delta),
                (ycenter + yy - delta))
            self.log.info(pstr)
            return (amp,
                    xcenter + xx - delta,
                    ycenter + yy - delta,
                    xsigma,
                    ysigma)

        except (RuntimeError, UserWarning) as e:
            self.log.info("Warning: {0:s}, returning zeros "
                          "for fit".format(str(e)))
            return (0, 0, 0, 0, 0)

    def radial_profile(self, x, y, data=None, form=None,
                       genplot=True, fig=None):
        """Display the radial profile plot (intensity vs radius) for the object.

        From the parameters Dictionary:
        If pixel is True, then every pixel at each radius is plotted.
        If pixel is False, then the sum of all pixels in integer bins is plotted

        Background may be subtracted and centering can be done with a
        2D Gaussian fit. These options are read from the plot parameters dict.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        form: string
            The string name of the form of the fit to use
        genplot: bool
            Generate the plot if True, else retfurn the fit data

        """
        pars = self.radial_profile_pars

        subtract_background = bool(pars["background"][0])
        if not photutils_installed and subtract_background:
            self.log.warning("Install photutils to enable "
                             "background subtraction")
            subtract_background = False

        if data is None:
            data = self._data

        getdata = bool(pars["getdata"][0])
        center = pars["center"][0]

        # be careful with the clipping since most
        # of the data will be near the low value
        clip_on = pars["clip"][0]
        if clip_on:
            sig_factor = pars["sigma"][0]
        else:
            sig_factor = 0

        fitplot = bool(pars["fitplot"][0])

        if fitplot:
            if form is None:
                fitform = getattr(models, pars["func"][0])
            else:
                if form not in self._fit_models:
                    msg = "{0:s} not supported for fitting".format(form)
                    self.log.info(msg)
                    raise ValueError(msg)
                else:
                    fitform = getattr(models, form)

        # cut the data down to size and center cutout
        datasize = int(pars["rplot"][0])
        if datasize < 3:
            self.log.info("Insufficient pixels, resetting chunk size to 3.")
            datasize = 3

        if center:
            # reset delta for small arrays
            # make it odd if it's even
            if ((datasize % 2) == 0):
                datasize = datasize + 1
            xx = int(x)
            yy = int(y)
            #  flipped from xpa
            data_chunk = data[yy - datasize:yy + datasize,
                              xx - datasize:xx + datasize]
            amp, centerx, centery, sigmax, sigmay = self.gauss_center(xx, yy, data, delta=datasize)

        else:
            centery = y
            centerx = x

        icenterx = int(centerx)
        icentery = int(centery)

        # fractional center, help with precision errors to 1000th pixel
        xfrac = round(centerx - icenterx, 2)
        yfrac = round(centery - icentery, 2)

        # just grab the data box centered on the object
        data_chunk = data[icentery - datasize:icentery + datasize,
                          icenterx - datasize:icenterx + datasize]

        y, x = np.indices(data_chunk.shape)  # index of all pixels
        y = y - datasize
        x = x - datasize
        r = np.sqrt((x-xfrac)**2 + (y-yfrac)**2)

        indices = np.argsort(r.flat)  # sorted indices

        if pars["pixels"][0]:
            flux = data_chunk.ravel()[indices]
            radius = r.ravel()[indices]

        else:  # sum the flux in integer bins
            radius = r.ravel()[indices].astype(np.int)
            flux = np.bincount(radius, data_chunk.ravel()[indices])
            radbc = np.bincount(radius)
            flux = flux / radbc
            radius = np.arange(len(flux))

        # Get a background measurement
        if subtract_background:
            inner = pars["skyrad"][0]
            width = pars["width"][0]
            annulus_apertures = photutils.CircularAnnulus((centerx, centery),
                                                          r_in=inner,
                                                          r_out=inner+width)
            bkgflux_table = photutils.aperture_photometry(data,
                                                          annulus_apertures)

            # to calculate the mean local background, divide the circular
            # annulus aperture sums by the area of the circular annulus.
            # The bkg sum with the circular aperture is then
            # the mean local background times the circular apreture area.
            annulus_area = annulus_apertures.area()
            sky_per_pix = float(bkgflux_table['aperture_sum'] /
                                annulus_area)

            # don't add flux
            if sky_per_pix < 0:
                sky_per_pix = 0
                self.log.info("Sky background negative, setting to zero")
            self.log.info("Background per pixel: {0:f}".format(sky_per_pix))

            flux -= sky_per_pix

            if getdata:
                self.log.info("Sky per pixel: {0} using "
                              "(rad={1}->{2})".format(sky_per_pix,
                                                      inner, inner + width))
        if getdata:
            info = "\nat (x,y)={0:f},{1:f}\n".format(centerx, centery)
            self.log.info(info)
            self.log.info(radius, flux)

        # Fit the functional form to the radial profile flux
        # TODO: Ignore sky subtracted pixels that push flux
        # below zero?
        if fitplot:
            fline = np.linspace(0, datasize, 100)  # finer sample
            # fit model to data
            if fitform.name is "Gaussian1D":
                fitted = math_helper.fit_gauss_1d(radius, flux,
                                                  sigma_factor=sig_factor,
                                                  center_at=0,
                                                  weighted=True)

                fwhmx, fwhmy = math_helper.gfwhm(fitted.stddev_0.value)
                legend = ("Max. pix. flux = {0:9.3f}\n"
                          "amp = {1:9.3f}\n"
                          "fwhm = {2:9.3f}".format(np.max(flux),
                                                   fitted.amplitude_0.value,
                                                   fwhmx))
                self.log.info(legend)
                legendx = datasize / 2
                legendy = np.max(flux) / 2

            elif fitform.name is "Moffat1D":
                fitted = math_helper.fit_moffat_1d(flux,
                                                   sigma_factor=sig_factor,
                                                   center_at=0,
                                                   weighted=True)
                mfwhm = math_helper.mfwhm(fitted.alpha_0.value,
                                          fitted.gamma_0.value)
                legend = ("Max. pix. flux = {0:9.3f}\n"
                          "amp = {1:9.3f}\n"
                          "fwhm = {2:9.3f}".format(np.max(flux),
                                                   fitted.amplitude_0.value,
                                                   mfwhm))
                legendx = datasize / 2
                legendy = np.max(flux) / 2

            elif fitform.name is "MexicanHat1D":
                fitted = math_helper.fit_mex_hat_1d(flux,
                                                    sigma_factor=sig_factor,
                                                    center_at=0,
                                                    weighted=True)
                legend = ("Max. pix. flux = {0:9.3f}\n".format(np.max(flux)))
                legendx = datasize / 2
                legendy = np.max(flux) / 2

            if fitted is None:
                msg = "Problem with the {0:s} fit".format(fitform.name)
                self.log.info(msg)
                raise ValueError(msg)

            yfit = fitted(fline)

        #  finish the plot
        #  TODO: users may get error if they use this without a display
        #  and request data back but forget to set genplot=False
        if genplot:
            pfig = fig
            if fig is None:
                fig = plt.figure(self._figure_name)
            fig.clf()
            fig.add_subplot(111)
            ax = fig.gca()

            if subtract_background:
                ytitle = ("Flux ( sky/pix = {0:8.2f} )".format(sky_per_pix))
            else:
                ytitle = pars["ylabel"][0]
            ax.set_xlabel(pars["xlabel"][0])
            ax.set_ylabel(ytitle)

            if bool(pars["pointmode"][0]):
                ax.plot(radius, flux, pars["marker"][0])
            else:
                ax.plot(radius, flux)
            ax.set_ylim(0,)

            if pars["title"][0] is None:
                if fitplot:
                    title = ("Radial Profile at ({0:d},{1:d}) with {2:s}"
                             .format(icenterx, icentery, fitform.name))
                else:
                    title = "Radial Profile for {0} {1}".format(icenterx,
                                                                icentery)
            else:
                title = pars["title"][0]

            if fitplot:
                ax.plot(fline, yfit, linestyle='-', c='r', label=fitform.name)
                ax.set_xlim(0, datasize, 0.5)
                ax.text(legendx, legendy, legend)

            ax.set_title(title)

            if pfig is None and 'nbagg' not in get_backend().lower():
                plt.draw()
                plt.pause(0.001)
            else:
                fig.canvas.draw()
        else:
            return radius, flux

    def curve_of_growth(self, x, y, data=None, genplot=True, fig=None):
        """Display a curve of growth plot.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        fig: figure name for redirect
            Used for interaction with the ginga GUI

        Notes
        -----
        the object photometry is taken from photutils

        """
        if not photutils_installed:
            self.log.warning("Install photutils to enable")
        else:

            if data is None:
                data = self._data

            delta = 10  # chunk size to find center
            subpixels = 10  # for line fit later

            # center using a 2d gaussian
            if self.curve_of_growth_pars["center"][0]:
                # pull out a small chunk
                amp, centerx, centery, sigma, sigmay = \
                    self.gauss_center(x, y, data, delta=delta)
            else:
                centery = y
                centerx = x
            centerx = int(centerx)
            centery = int(centery)

            # now grab aperture sums going out from that central pixel
            inner = self.curve_of_growth_pars["buffer"][0]
            width = self.curve_of_growth_pars["width"][0]
            router = self.curve_of_growth_pars["rplot"][0]
            getdata = bool(self.curve_of_growth_pars["getdata"][0])

            radius = list()
            flux = list()
            rapert = int(router) + 1
            for rad in range(1, rapert, 1):
                aper_flux, annulus_sky, skysub_flux = self._aperture_phot(
                    centerx, centery, data, radsize=rad, sky_inner=inner,
                    skywidth=width, method="exact", subpixels=subpixels)
                radius.append(rad)
                if self.curve_of_growth_pars["background"][0]:
                    if inner < router:
                        warnings.warn(
                            "Your sky annulus is inside your \
                            photometry radius rplot")
                    flux.append(skysub_flux)
                else:
                    flux.append(aper_flux)
            if getdata:
                rapert = np.arange(1, rapert, 1)
                info = "\nat (x,y)={0:d},{1:d}\nradii:{2}\nflux:{3}".format(
                    int(centerx), int(centery), rapert, flux)
                self.log.info(info)
            if genplot:
                pfig = fig
                if fig is None:
                    fig = plt.figure(self._figure_name)
                fig.clf()
                fig.add_subplot(111)
                ax = fig.gca()

                if self.curve_of_growth_pars["title"][0] is None:
                    title = "{0}: {1} {2}".format(self._datafile,
                                                  int(x),
                                                  int(y))
                else:
                    title = self.curve_of_growth_pars["title"][0]

                ax.set_xlabel(self.curve_of_growth_pars["xlabel"][0])
                ax.set_ylabel(self.curve_of_growth_pars["ylabel"][0])
                ax.plot(radius, flux, 'o')
                ax.set_title(title)

                if pfig is None and 'nbagg' not in get_backend().lower():
                    plt.draw()
                    plt.pause(0.001)
                else:
                    fig.canvas.draw()

            else:
                return rapert, flux

    def _aperture_phot(self, x, y, data=None, radsize=1,
                       sky_inner=5, skywidth=5,
                       method="subpixel", subpixels=4):
        """Perform sky subtracted aperture photometry.

        uses photutils functions, photutil must be installed

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        radsize: int
            Size of the radius
        sky_inner: int
            Inner radius of the sky annulus
        skywidth: int
            Width of the sky annulus
        method: string
            Pixel sampling method to use
        subpixels: int
            How many subpixels to use

        Notes
        -----
        background is taken from sky annulus pixels, check into
        masking bad pixels
        """
        if not photutils_installed:
            self.log.warning("Install photutils to enable")
        else:

            if data is None:
                data = self._data

            apertures = photutils.CircularAperture((x, y), radsize)
            rawflux_table = photutils.aperture_photometry(
                data,
                apertures,
                subpixels=1,
                method="center")

            outer = sky_inner + skywidth
            annulus_apertures = photutils.CircularAnnulus(
                (x, y), r_in=sky_inner, r_out=outer)
            bkgflux_table = photutils.aperture_photometry(
                data,
                annulus_apertures)

            # to calculate the mean local background, divide the circular
            # annulus aperture sums
            # by the area of the circular annulus. The bkg sum within the
            # circular aperture is then
            # then mean local background times the circular apreture area.
            aperture_area = apertures.area()
            annulus_area = annulus_apertures.area()

            bkg_sum = (
                bkgflux_table['aperture_sum'] *
                aperture_area /
                annulus_area)[0]
            skysub_flux = rawflux_table['aperture_sum'][0] - bkg_sum

            return (
                float(rawflux_table['aperture_sum'][0]), bkg_sum, skysub_flux)

    def histogram(self, x, y, data=None, genplot=True, fig=None):
        """Calulate a histogram of the data values.

        Parameters
        ----------
        x: int, required
            The x location of the object
        y: int, required
            The y location of the object
        data: numpy array, optional
            The data array to work on
        genplot: boolean, optional
            If false, returns the hist, bin_edges tuple
        fig: figure name for redirect
            Used for interaction with the ginga GUI

        Notes
        -----
        This functional originally used the pylab histogram routine for
        plotting. In order to accomodate returning just the histogram data,
        this was changed to the numpy histogram, with a subsequent plot if
        genplot is True.

        Does not yet support numpy v1.11 strings for bin estimation.

        """
        if data is None:
            data = self._data

        deltax = int(self.histogram_pars["ncolumns"][0] / 2.)
        deltay = int(self.histogram_pars["nlines"][0] / 2.)
        yf = int(y)
        xf = int(x)

        data_cut = data[yf - deltay:yf + deltay, xf - deltax:xf + deltax]

        # mask data for min and max intensity specified
        if self.histogram_pars["z1"][0]:
            mini = float(self.histogram_pars["z1"][0])
        else:
            mini = np.min(data_cut)

        if self.histogram_pars["z2"][0]:
            maxi = float(self.histogram_pars["z2"][0])
        else:
            maxi = np.max(data_cut)

        lt = (data_cut < maxi)
        gt = (data_cut > mini)

        total_mask = lt * gt
        flat_data = data_cut[total_mask].flatten()

        if not maxi:
            maxi = np.max(data_cut)
        if not mini:
            mini = np.min(data_cut)
        num_bins = int(self.histogram_pars["nbins"][0])

        if genplot:
            pfig = fig
            if fig is None:
                fig = plt.figure(self._figure_name)
            fig.clf()
            fig.add_subplot(111)
            ax = fig.gca()

            if self.histogram_pars["title"][0] is None:
                title = "{0}: {1} {2}".format(self._datafile, int(x), int(y))
            else:
                title = self.histogram_pars["title"][0]
            ax.set_title(title)
            ax.set_xlabel(self.histogram_pars["xlabel"][0])
            ax.set_ylabel(self.histogram_pars["ylabel"][0])

            if self.histogram_pars["logx"][0]:
                ax.set_xscale("log")
            if self.histogram_pars["logy"][0]:
                ax.set_yscale("log")
            n, bins, patches = ax.hist(flat_data, num_bins,
                                       range=[mini, maxi],
                                       normed=False,
                                       facecolor='green',
                                       alpha=0.5,
                                       histtype='bar')
            self.log.info("{0} bins "
                          "range:[{1},{2}]".format(num_bins, mini, maxi))

            if pfig is None and 'nbagg' not in get_backend().lower():
                plt.draw()
                plt.pause(0.001)
            else:
                fig.canvas.draw()
        else:
            hist, bin_edges = np.histogram(flat_data,
                                           num_bins,
                                           range=[mini, maxi],
                                           normed=False)
            return hist, bin_edges

    def contour(self, x, y, data=None, fig=None):
        """plot contours in a region around the specified location.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        fig: figure for redirect
            Used for interaction with the ginga GUI

        """
        if data is None:
            data = self._data

        pfig = fig
        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca()

        if self.contour_pars["title"][0] is None:
            title = "{0} {1} {2}".format(self._datafile, int(x), int(y))
        else:
            title = self.contour_pars["title"][0]
        ax.set_title(title)
        ax.set_xlabel(self.contour_pars["xlabel"][0])
        ax.set_ylabel(self.contour_pars["ylabel"][0])
        ncont = self.contour_pars["ncontours"][0]
        colormap = self.contour_pars["cmap"][0]
        lsty = self.contour_pars["linestyles"][0]

        self.log.info("contour centered at: {0} {1}".format(x, y))
        deltax = int(self.contour_pars["ncolumns"][0] / 2.)
        deltay = int(self.contour_pars["nlines"][0] / 2.)
        xx = int(x)
        yy = int(y)
        data_cut = data[yy - deltay:yy + deltay, xx - deltax:xx + deltax]
        plt.rcParams['xtick.direction'] = 'out'
        plt.rcParams['ytick.direction'] = 'out'

        X, Y = np.meshgrid(np.arange(0, deltax, 0.5) + x - deltax / 2.,
                           np.arange(0, deltay, 0.5) + y - deltay / 2.)

        C = ax.contour(
            X,
            Y,
            data_cut,
            ncont,
            linewidths=.5,
            colors='black',
            linestyles=lsty)
        # make the filled contour
        ax.contourf(X, Y, data_cut, ncont, alpha=.75, cmap=colormap)
        if self.contour_pars["label"][0]:
            ax.clabel(C, inline=1, fontsize=10, fmt="%5.3f")

        if pfig is None and 'nbagg' not in get_backend().lower():
            plt.draw()
            plt.pause(0.001)
        else:
            fig.canvas.draw()

    def surface(self, x, y, data=None, fig=None):
        """plot a surface around the specified location.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        fig: figure for redirect
            Used for interaction with the ginga GUI
        """
        from mpl_toolkits.mplot3d import Axes3D
        from matplotlib.ticker import LinearLocator, FormatStrFormatter

        if data is None:
            data = self._data
        pfig = fig
        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca(projection='3d')

        title = self.surface_pars["title"][0]
        if title is None:
            title = "{0}: {1} {2}".format(self._datafile, int(x), int(y))
        ax.set_title(title)
        ax.set_xlabel(self.surface_pars["xlabel"][0])
        ax.set_ylabel(self.surface_pars["ylabel"][0])
        if self.surface_pars["zlabel"][0]:
            ax.set_zlabel("Flux")
        fancy = self.surface_pars["fancy"][0]
        deltax = self.surface_pars["ncolumns"][0]
        deltay = self.surface_pars["nlines"][0]

        minx = int(x - deltax) if x - deltax > 0 else 0
        miny = int(y - deltay) if y - deltay > 0 else 0
        maxx = int(x + deltax) if x + deltax < data.shape[-1] else data.shape[0]
        maxy = int(y + deltay) if y + deltay < data.shape[0] else data.shape[0]

        X = np.arange(minx, maxx, 1)
        Y = np.arange(miny, maxy, 1)

        X, Y = np.meshgrid(X, Y)
        Z = data[miny:maxy, minx:maxx]
        if self.surface_pars["floor"][0]:
            zmin = float(self.surface_pars["floor"][0])
        else:
            zmin = np.min(Z)
        if self.surface_pars["ceiling"][0]:
            zmax = float(self.surface_pars["ceiling"][0])
        else:
            zmax = np.max(Z)

        stride = int(self.surface_pars["stride"][0])
        if fancy:
            surf = ax.plot_surface(
                X, Y, Z, rstride=stride, cstride=stride,
                cmap=self.surface_pars["cmap"][0], alpha=0.6)
        else:
            surf = ax.plot_surface(X, Y, Z, rstride=stride, cstride=stride,
                                   cmap=self.surface_pars["cmap"][0],
                                   linewidth=0, antialiased=False)

        ax.zaxis.set_major_locator(LinearLocator(10))
        ax.zaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        ax.set_zlim(zmin, zmax)

        if fancy:
            xmin = minx
            ymax = maxy
            cset = ax.contour(
                X,
                Y,
                Z,
                zdir='z',
                offset=zmax,
                cmap=self.surface_pars["cmap"][0])
            cset = ax.contour(
                X,
                Y,
                Z,
                zdir='x',
                offset=xmin,
                cmap=self.surface_pars["cmap"][0])
            cset = ax.contour(
                X,
                Y,
                Z,
                zdir='y',
                offset=ymax,
                cmap=self.surface_pars["cmap"][0])

        fig.colorbar(surf, shrink=0.5, aspect=5)
        if self.surface_pars["azim"][0]:
            ax.view_init(elev=10., azim=float(self.surface_pars["azim"][0]))

        if pfig is None and 'nbagg' not in get_backend().lower():
            plt.draw()
            plt.pause(0.001)
        else:
            fig.canvas.draw()

    def cutout(self, x, y, data=None, size=None, fig=None):
        """Make a fits cutout around the pointer location without wcs.

        Parameters
        ----------
        x: int
            The x location of the object
        y: int
            The y location of the object
        data: numpy array
            The data array to work on
        size: int
            The radius of the cutout region
        fig: figure for redirect
            Used for interaction with the ginga GUI
        """
        if data is None:
            data = self._data

        if size is None:
            size = self.cutout_pars["size"][0]

        xx = int(x)
        yy = int(y)
        prefix = "cutout_{0}_{1}_".format(xx, yy)
        fname = tempfile.mkstemp(prefix=prefix, suffix=".fits", dir="./")[-1]
        cutout = data[yy - size:yy + size, xx - size:xx + size]
        hdu = fits.PrimaryHDU(cutout)
        hdulist = fits.HDUList([hdu])
        hdulist[0].header['EXTEND'] = False
        hdulist.writeto(fname)
        self.log.info("Cutout at ({0},{1}) saved to {2:s}".format(xx, yy, fname))

    def register(self, user_funcs):
        """register a new imexamine function made by the user as an option.

        Parameters
        ----------
        user_funcs: dict
            Contains a dictionary where each key is the binding for the
            (function,description) tuple

        Notes
        -----
        The new binding will be added to the dictionary of imexamine functions
        as long as the key is unique. The new functions do not have to have
        default dictionaries associated with them.
        """
        if not isinstance(user_funcs, type(dict())):
            warnings.warn("Your input needs to be a dictionary")

        for key in user_funcs.keys():
            if key in self.imexam_option_funcs.keys():
                warnings.warn("{0:s} is not a unique key".format(key))
                warnings.warn("{0:s}".format(self.imexam_option_funcs[key]))
                raise ValueError("{0:s} is not a unique key".format(key))
            elif key == 'q':
                warnings.warn("q is reserved as the quit key")
                raise ValueError("q is reserved for the quit key")
            else:
                func_name = user_funcs[key][0].__name__
                self._add_user_function(user_funcs[key][0])
                self.imexam_option_funcs[key] = (
                    self.__getattribute__(func_name), user_funcs[key][1])
                self.log.info(
                    "User function: {0:s} added to imexam options with "
                    "key {1:s}".format(func_name, key))

    @classmethod
    def _add_user_function(cls, func):
        import types
        if PY3:
            return setattr(cls, func.__name__, types.MethodType(func, cls))
        else:
            return setattr(cls, func.__name__,
                           types.MethodType(func, None, cls))

    def set_aper_phot_pars(self, user_dict=None):
        """the user may supply a dictionary of par settings."""
        if not user_dict:
            self.aper_phot_pars = imexam_defpars.aper_phot_pars
        else:
            self.aper_phot_pars = user_dict

    def set_radial_pars(self):
        """set parameters for radial profile plots."""
        self.radial_profile_pars = imexam_defpars.radial_profile_pars

    def set_curve_pars(self):
        """set parameters for curve of growth plots."""
        self.curve_of_growth_pars = imexam_defpars.curve_of_growth_pars

    def set_surface_pars(self):
        """set parameters for surface plots."""
        self.surface_pars = imexam_defpars.surface_pars

    def set_line_fit_pars(self):
        """set parameters for 1D line fit plots."""
        self.line_fit_pars = imexam_defpars.line_fit_pars

    def set_column_fit_pars(self):
        """set parameters for 1D line fit plots."""
        self.column_fit_pars = imexam_defpars.column_fit_pars

    def set_contour_pars(self):
        """set parameters for contour plots."""
        self.contour_pars = imexam_defpars.contour_pars

    def set_histogram_pars(self):
        """set parameters for histogram plots."""
        self.histogram_pars = imexam_defpars.histogram_pars

    def set_lineplot_pars(self):
        """set parameters for line plots."""
        self.lineplot_pars = imexam_defpars.lineplot_pars

    def set_colplot_pars(self):
        """set parameters for column plots."""
        self.colplot_pars = imexam_defpars.colplot_pars

    def set_cutout_pars(self):
        """set parameters for cutout images."""
        self.cutout_pars = imexam_defpars.cutout_pars

    def reset_defpars(self):
        """set all pars to their defaults."""
        self._define_pars()
