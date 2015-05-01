# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""This class implements IRAF/imexamine type capabilities"""

from __future__ import print_function, division, absolute_import

import numpy as np
import warnings
import matplotlib.pyplot as plt
# turn on interactive mode for plotting
plt.ion()

from scipy.optimize import curve_fit
import time
import logging
from copy import deepcopy
import inspect

# enable display plot in iPython notebook
from IPython.display import Image
import StringIO

try:
    import photutils
    photutils_installed = True
except ImportError:
    print(
        "photutils not installed, photometry functionality in imexam() not available")
    photutils_installed = False

from . import math_helper
from . import imexam_defpars

__all__ = ["Imexamine"]


class Imexamine(object):

    def __init__(self):
        """ do imexamine like routines on the current frame

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
        self.sleep_time = 1e-6    # for plotting convenience
        # let users have multiple plot windows, the list stores their names
        self._plot_windows = list()
        # this contains the name of the current plotting window
        self._figure_name = "imexam"

        self._plot_windows.append(self._figure_name)

    def set_option_funcs(self):
        """Define the dictionary which maps imexam option keys to their functions


         Notes
         -----
         The user can modify this dictionary to add or change options,
         the first item in the tuple is the associated function
         the second item in the tuple is the description of what the function
         does when that key is pressed
        """

        self.imexam_option_funcs = {'a': (self.aper_phot, 'aperture sum, with radius region_size '),
                                    'j': (self.line_fit, '1D [gaussian|moffat] line fit '),
                                    'k': (self.column_fit, '1D [gaussian|moffat] column fit'),
                                    'm': (self.report_stat, 'square region stats, in [region_size],defayult is median'),
                                    'x': (self.show_xy_coords, 'return x,y,value of pixel'),
                                    'y': (self.show_xy_coords, 'return x,y,value of pixel'),
                                    'l': (self.plot_line, 'return line plot'),
                                    'c': (self.plot_column, 'return column plot'),
                                    'r': (self.curve_of_growth_plot, 'return curve of growth plot'),
                                    'h': (self.histogram_plot, 'return a histogram in the region around the cursor'),
                                    'e': (self.contour_plot, 'return a contour plot in a region around the cursor'),
                                    's': (self.save_figure, 'save current figure to disk as [plot_name]'),
                                    'b': (self.gauss_center, 'return the gauss fit center of the object'),
                                    'w': (self.surface_plot, 'display a surface plot around the cursor location'),
                                    '2': (self.new_plot_window, 'make the next plot in a new window'),
                                    }

    def print_options(self):
        """print the imexam options to screen"""
        keys = self.get_options()
        for key in keys:
            print("%s\t%s" % (key, self.option_descrip(key)))
        print()

    def do_option(self, x, y, key):
        """run the option

        Parameters
        ----------

        x: int
            The x location of the cursor or data point

        y: int
            The y location of the cursor or data point

        key: string
            The key which was pressed

        """
        print("pressed: {0}".format(key))
        self.imexam_option_funcs[key][0](x, y, self._data)

    def get_options(self):
        """return the imexam options as a key list"""
        keys = sorted(self.imexam_option_funcs.keys())
        return keys

    def option_descrip(self, key, field=1):
        """return the looked up dictionary of options


        Parameters
        ----------
        key: string
            The key which was pressed, it relates to the function to call

        field: int
            This tells where in the option dictionary the function name can be found


        """
        return self.imexam_option_funcs[key][field]

    def set_data(self, data=np.zeros(0)):
        """initialize the data that imexamine uses"""
        self._data = data

    def set_plot_name(self, filename=None):
        """set the default plot name for the "s" key

        Parameters
        ----------
        filename: string
            The name which is used to save the current plotting window to a file
            The extension on the name decides which file type is used


        """
        if not filename:
            warnings.warn("No filename provided")
        else:
            self.plot_name = filename

    def get_plot_name(self):
        """return the default plot name"""
        print(self.plot_name)

    def _define_default_pars(self):
        """set all pars to their defaults which are stored in a file with dicts"""

        self.aperphot_def_pars = imexam_defpars.aperphot_pars
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

        self._define_local_pars()

    def _define_local_pars(self):
        """set a copy of the default pars that users can alter"""

        self.aperphot_pars = deepcopy(self.aperphot_def_pars)
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

    def unlearn_all(self):
        """reset the default parameters for all functions

        Haven't decided how to reset the parameters for just one function yet
        """
        self._define_local_pars()

    def new_plot_window(self, x, y, data):
        """make the next plot in a new plot window


        Notes
        -----
        x,y, data, are not used here, but the calls are setup to take them
        for all imexam options. Is there a better way to do the calls in general?
        Once the new plotting window is open all plots will be directed towards it
        The old window cannot be used again.

        """
        counter = len(self._plot_windows) + 1
        self._figure_name = "imexam" + str(counter)
        self._plot_windows.append(self._figure_name)
        print("Plots now directed towards {0:s}".format(self._figure_name))

    def plot_line(self, x, y, data, fig=None):
        """line plot of data at point x"""

        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca()
        ax.set_title(
            "{0:s}  line={1:d}".format(
                self.lineplot_pars["title"][0], int(
                    y + 1)))
        ax.set_xlabel(self.lineplot_pars["xlabel"][0])
        ax.set_ylabel(self.lineplot_pars["ylabel"][0])

        if not self.lineplot_pars["xmax"][0]:
            xmax = len(data[y, :])
        else:
            xmax = self.lineplot_pars["xmax"][0]
        ax.set_xlim(self.lineplot_pars["xmin"][0], xmax)

        if self.lineplot_pars["logx"][0]:
            ax.set_xscale("log")
        if self.lineplot_pars["logy"][0]:
            ax.set_yscale("log")

        if self.lineplot_pars["pointmode"][0]:
            ax.plot(data[y, :], self.lineplot_pars["marker"][0])
        else:
            ax.plot(data[y, :])

        plt.draw()
        plt.show(block=False)
        time.sleep(self.sleep_time)

    def plot_column(self, x, y, data, fig=None):
        """column plot of data at point y"""

        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca()
        ax.set_title(
            "{0:s}  column={1:d}".format(
                self.colplot_pars["title"][0], int(
                    x + 1)))
        ax.set_xlabel(self.colplot_pars["xlabel"][0])
        ax.set_ylabel(self.colplot_pars["ylabel"][0])

        if not self.colplot_pars["xmax"][0]:
            xmax = len(data[:, x])
        else:
            xmax = self.colplot_pars["xmax"][0]
        ax.set_xlim(self.colplot_pars["xmin"][0], xmax)

        if self.colplot_pars["logx"][0]:
            ax.set_xscale("log")

        if self.colplot_pars["logy"][0]:
            ax.set_yscale("log")
        if self.colplot_pars["pointmode"][0]:
            ax.plot(data[:, x], self.colplot_pars["marker"][0])
        else:
            ax.plot(data[:, x])

        plt.draw()
        plt.show(block=False)
        time.sleep(self.sleep_time)

    def show_xy_coords(self, x, y, data):
        """print the x,y,value to the screen"""
        info = "{0} {1}  {2}".format(x + 1, y + 1, data[(y), (x)])
        print(info)
        logging.info(info)

    def report_stat(self, x, y, data):
        """report the median of values in a box with side region_size"""
        region_size = self.report_stat_pars["region_size"][0]
        resolve = True
        try:
            stat = getattr(np, self.report_stat_pars["stat"][0])
        except AttributeError:
            warnings.warn("Invalid stat specified")
            resolve = False
        if resolve:
            dist = region_size / 2
            xmin = int(x - dist)
            xmax = int(x + dist)
            ymin = int(y - dist)
            ymax = int(y + dist)
            pstr = "[{0:d}:{1:d},{2:d}:{3:d}] {4:s}: {5:f}".format(
                xmin, xmax, ymin, ymax, stat.func_name, (stat(data[ymin:ymax, xmin:xmax])))
            print(pstr)
            logging.info(pstr)

    def save_figure(self, x, y, data):
        """save the figure that's currently displayed"""
        fig = plt.figure(self._figure_name)
        ax = fig.gca()
        plt.savefig(self.plot_name)
        pstr = "plot saved to {0:s}".format(self.plot_name)
        print(pstr)
        logging.info(pstr)

    def aper_phot(self, x, y, data):
        """Perform aperture photometry, uses photutils functions, photutils must be available

        """
        sigma = 0.  # no centering
        amp = 0.  # no centering
        if not photutils_installed:
            print("Install photutils to enable")
        else:
            if self.aperphot_pars["center"][0]:
                center = True
                delta = 10
                popt = self.gauss_center(x, y, data, delta=delta)
                if 5 > popt.count(0) > 1:  # an error occurred in centering
                    warnings.warn(
                        "Problem fitting center, using original coordinates")
                else:
                    amp, x, y, sigma, offset = popt

            radius = int(self.aperphot_pars["radius"][0])
            width = int(self.aperphot_pars["width"][0])
            inner = int(self.aperphot_pars["skyrad"][0])
            subsky = bool(self.aperphot_pars["subsky"][0])

            outer = inner + width

            apertures = photutils.CircularAperture((x, y), radius)
            rawflux_table = photutils.aperture_photometry(
                data,
                apertures,
                subpixels=1,
                method="center")

            if subsky:
                annulus_apertures = photutils.CircularAnnulus(
                    (x, y), r_in=inner, r_out=outer)
                bkgflux_table = photutils.aperture_photometry(
                    data,
                    annulus_apertures)

                # to calculate the mean local background, divide the circular annulus aperture sums
                # by the area fo teh circular annuls. The bkg sum with the circular aperture is then
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
            magzero = float(self.aperphot_pars["zmag"][0])
            mag = magzero - 2.5 * (np.log10(total_flux))

            pheader = (
                "x\ty\tradius\tflux\tmag(zpt={0:0.2f})\tsky\t".format(magzero)).expandtabs(15)
            if center:
                pheader += ("fwhm")
                pstr = "\n{0:.2f}\t{1:0.2f}\t{2:d}\t{3:0.2f}\t{4:0.2f}\t{5:0.2f}\t{6:0.2f}".format(
                    x + 1, y + 1, radius, total_flux, mag, sky_per_pix, math_helper.gfwhm(sigma)).expandtabs(15)
            else:
                pstr = "\n{0:0.2f}\t{1:0.2f}\t{2:d}\t{3:0.2f}\t{4:0.2f}\t{5:0.2f}".format(
                    x + 1, y + 1, radius, total_flux, mag, sky_per_pix,).expandtabs(15)

            print(pheader + pstr)
            logging.info(pheader + pstr)

    def line_fit(self, x, y, data, form=None, subsample=4, fig=None):
        """compute the 1d  fit to the line of data using the specified form


        Parameters
        ----------
        form: string
            This is the functional form specified  line fit parameters
            Currently gaussian or moffat

        subsample: int
            used to draw the fitted function on a finer scale than the data
            delta is the range of data values to use around the x,y location
            form is the functional form to use

        Notes
        -----
        The background is currently ignored

        If centering is True in the parameter set, then the center is fit with a 2d gaussian

        """
        amp = 0
        sigma = 0
        if not form:
            form = getattr(math_helper, self.line_fit_pars["func"][0])

        delta = self.line_fit_pars["rplot"][0]

        if self.line_fit_pars["center"][0]:
            popt = self.gauss_center(x, y, data, delta=delta)
            if popt.count(0) > 1:  # an error occurred in centering
                centerx = x
                centery = y
                warnings.warn(
                    "Problem fitting center, using original coordinates")
            else:
                amp, x, y, sigma, offset = popt

        line = data[y, :]
        chunk = line[x - delta:x + delta]

        # use x location as the first estimate for the mean, use 20 pixel
        # distance to guess center
        argmap = {'a': amp, 'mu': len(chunk) / 2, 'sigma': sigma, 'b': 0}
        args = inspect.getargspec(form)[0][1:]  # get rid of "self"

        xline = np.arange(len(chunk))
        popt, pcov = curve_fit(
            form, xline, chunk, [
                argmap.get(
                    arg, 1) for arg in args])
        # do these so that it fits the real pixel range of the data
        fitx = np.arange(len(xline), step=1. / subsample)
        fity = form(fitx, *popt)

        # calculate the std about the mean
        # make a plot
        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca()
        ax.set_xlabel(self.line_fit_pars["xlabel"][0])
        ax.set_ylabel(self.line_fit_pars["ylabel"][0])
        if self.line_fit_pars["logx"][0]:
            ax.set_xscale("log")
        if self.line_fit_pars["logy"][0]:
            ax.set_yscale("log")

        if self.line_fit_pars["pointmode"][0]:
            ax.plot(xline + x - delta, chunk, 'o', label="data")
        else:
            ax.plot(xline + x - delta, chunk, label="data", linestyle='-')

        if self.line_fit_pars["func"][0] == "gaussian":
            sigma = np.abs(popt[2])
            fwhm = math_helper.gfwhm(sigma)
            fitmean = popt[1] + x - delta
        elif self.line_fit_pars["func"][0] == "moffat":
            alpha = popt[0]
            beta = popt[1]
            fwhm = math_helper.mfwhm(alpha, beta)
            fitmean = popt[2] + x - delta
        else:
            warnings.warn("Unsupported functional form used in line_fit")
            raise ValueError

        ax.set_title("{0:s}  mean = {1:s}, fwhm= {2:s}".format(
            self.line_fit_pars["title"][0], str(fitmean), str(fwhm)))
        ax.plot(
            fitx +
            x -
            delta,
            fity,
            c='r',
            label=str(
                form.__name__) +
            " fit")
        plt.legend()
        plt.draw()
        plt.show(block=False)
        time.sleep(self.sleep_time)
        pstr = "({0:d},{1:d}) mean={2:0.3f}, fwhm={3:0.3f}".format(
            int(x + 1), int(y + 1), fitmean, fwhm)
        print(pstr)
        logging.info(pstr)

    def column_fit(self, x, y, data, form=None, subsample=4, fig=None):
        """compute the 1d  fit to the column of data

        Parameters
        ----------
        form: string
            This is the functional form specified  line fit parameters
            Currently gaussian or moffat

        subsample: int
            used to draw the fitted gaussian

        Notes
        -----
        delta is the range of data values to use around the x,y location
        The background is currently ignored
        if centering is True, then the center is fit with a 2d gaussian

        """

        sigma = 0
        amp = 0
        if not form:
            form = getattr(math_helper, self.line_fit_pars["func"][0])

        delta = self.column_fit_pars["rplot"][0]

        if self.column_fit_pars["center"][0]:
            popt = self.gauss_center(x, y, data, delta=delta)
            if popt.count(0) > 1:  # an error occurred in centering
                centerx = x
                centery = y
                warnings.warn(
                    "Problem fitting center, using original coordinates")
            else:
                amp, x, y, sigma, offset = popt

        line = data[:, x]
        chunk = line[y - delta:y + delta]

        # use y location as the first estimate for the mean, use 20 pixel
        # distance to guess center
        argmap = {'a': amp, 'mu': len(chunk) / 2, 'sigma': sigma, 'b': 0}
        args = inspect.getargspec(form)[0][1:]  # get rid of "self"

        yline = np.arange(len(chunk))
        popt, pcov = curve_fit(
            form, yline, chunk, [
                argmap.get(
                    arg, 1) for arg in args])

        # do these so that it fits the real pixel range of the data
        fitx = np.arange(len(yline), step=1. / subsample)
        fity = form(fitx, *popt)

        # calculate the std about the mean
        # make a plot
        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca()
        ax.set_xlabel(self.column_fit_pars["xlabel"][0])
        ax.set_ylabel(self.column_fit_pars["ylabel"][0])
        if self.column_fit_pars["logx"][0]:
            ax.set_xscale("log")
        if self.column_fit_pars["logy"][0]:
            ax.set_yscale("log")

        if self.column_fit_pars["pointmode"][0]:
            ax.plot(yline + y - delta, chunk, 'o', label="data")
        else:
            ax.plot(yline + y - delta, chunk, linestyle='-', label="data")

        if self.column_fit_pars["func"][0] == "gaussian":
            sigma = np.abs(popt[2])
            fwhm = math_helper.gfwhm(sigma)
            fitmean = popt[1] + y - delta
        elif self.column_fit_pars["func"][0] == "moffat":
            fwhm = math_helper.mfwhm(popt[0], popt[1])
            fitmean = popt[2] + y - delta
        else:
            warnings.warn("Unsupported functional form used in column_fit")
            raise ValueError

        ax.set_title("{0:s}  mean = {1:s}, fwhm= {2:s}".format(
            self.column_fit_pars["title"][0], str(fitmean), str(fwhm)))
        ax.plot(
            fitx +
            y -
            delta,
            fity,
            c='r',
            label=str(
                form.__name__) +
            " fit")
        plt.legend()
        plt.draw()
        plt.show(block=False)
        time.sleep(self.sleep_time)
        pstr = "({0:d},{1:d}) mean={2:0.3f}, fwhm={3:0.2f}".format(
            int(x + 1), int(y + 1), fitmean, fwhm)
        print(pstr)
        logging.info(pstr)

    def gauss_center(self, x, y, data, delta=10):
        """return the 2d gaussian fit center

        Parameters
        ----------
        delta: int
            The range of data values to use around the x,y location for calculating the center

        """
        chunk = data[
            y -
            delta:y +
            delta,
            x -
            delta:x +
            delta]  # flipped from xpa
        try:
            amp, ycenter, xcenter, sigma, offset = math_helper.gauss_center(
                chunk)
            pstr = "xc={0:4f}\tyc={1:4f}".format(
                (xcenter + x - delta + 1), (ycenter + y - delta + 1))
            print(pstr)
            logging.info(pstr)
            return amp, (xcenter + x - delta), (ycenter +
                                                y - delta), sigma, offset
        except (RuntimeError, UserWarning) as e:
            print("Warning: {0:s}, returning zeros for fit".format(str(e)))
            return (0, 0, 0, 0, 0)

    def curve_of_growth_plot(self, x, y, data, fig=None):
        """
        display the radial profile plot for the star

        """
        if not photutils_installed:
            print("Install photutils to enable")
        else:

            delta = 10  # chunk size to find center
            subpixels = 10  # for line fit later

            # center using a 2d gaussian
            if self.curve_of_growth_pars["center"][0]:
                # pull out a small chunk
                popt = self.gauss_center(x, y, data, delta=delta)
                if popt.count(0) > 1:  # an error occurred in centering
                    centerx = x
                    centery = y
                    warnings.warn(
                        "Problem fitting center, using original coordinates")
                else:
                    amp, centerx, centery, sigma, offset = popt
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

            if fig is None:
                fig = plt.figure(self._figure_name)
            fig.clf()
            fig.add_subplot(111)
            ax = fig.gca()
            title = self.curve_of_growth_pars["title"][0]
            ax.set_xlabel(self.curve_of_growth_pars["xlabel"][0])
            ax.set_ylabel(self.curve_of_growth_pars["ylabel"][0])

            radius = list()
            flux = list()
            rapert = int(router) + 1
            for rad in range(1, rapert, 1):
                aper_flux, annulus_sky, skysub_flux = self._aperture_phot(
                    centerx, centery, data, radsize=rad, sky_inner=inner, skywidth=width, method="exact")
                radius.append(rad)
                if self.curve_of_growth_pars["background"][0]:
                    if inner < router:
                        warnings.warn(
                            "Your sky annulus is inside your photometry radius rplot")
                    flux.append(skysub_flux)
                else:
                    flux.append(aper_flux)
            if getdata:
                rapert = np.arange(1, rapert, 1)
                info = "\nat (x,y)={0:d},{1:d}\nradii:{2}\nflux:{3}".format(
                    int(centerx + 1), int(centery + 1), rapert, flux)
                print(info)
                logging.info(info)
            ax.plot(radius, flux, 'o')
            ax.set_title(title)
            plt.draw()
            plt.show(block=False)
            time.sleep(self.sleep_time)

    def _aperture_phot(self, x, y, data, radsize=1,
                       sky_inner=5, skywidth=5, method="subpixel", subpixels=4):
        """Perform sky subtracted aperture photometry, uses photutils functions, photutil must be installed

        Parameters
        ----------
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
           background is taken from sky annulus pixels, check into masking bad pixels

        """
        if not photutils_installed:
            print("Install photutils to enable")
        else:

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

            # to calculate the mean local background, divide the circular annulus aperture sums
            # by the area fo the circular annuls. The bkg sum with the circular aperture is then
            # then mean local background tims the circular apreture area.
            aperture_area = apertures.area()
            annulus_area = annulus_apertures.area()

            bkg_sum = (
                bkgflux_table['aperture_sum'] *
                aperture_area /
                annulus_area)[0]
            skysub_flux = rawflux_table['aperture_sum'][0] - bkg_sum

            return (
                float(rawflux_table['aperture_sum'][0]), bkg_sum, skysub_flux)

    def histogram_plot(self, x, y, data, fig=None):
        """plot a histogram of the pixel values in a region around the specified location"""

        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca()
        ax.set_title(self.histogram_pars["title"][0])
        ax.set_xlabel(self.histogram_pars["xlabel"][0])
        ax.set_ylabel(self.histogram_pars["ylabel"][0])
        if self.histogram_pars["logx"][0]:
            ax.set_xscale("log")
        if self.histogram_pars["logy"][0]:
            ax.set_yscale("log")
        deltax = np.ceil(self.histogram_pars["ncolumns"][0] / 2.)
        deltay = np.ceil(self.histogram_pars["nlines"][0] / 2.)

        data_cut = data[y - deltay:y + deltay, x - deltax:x + deltax]

        # mask data for min and max intensity specified
        if self.histogram_pars["z1"][0]:
            mini = float(self.histogram_pars["z1"][0])
        else:
            mini = np.min(data_cut)

        if self.histogram_pars["z2"][0]:
            maxi = float(self.histogram_pars["z2"][0])
        else:
            maxi = np.max(data_cut)

        # ltb=np.array(len(data_cut)*[True],bool)
        # gtb=np.array(len(data_cut)*[True],bool)

        lt = (data_cut < maxi)
        gt = (data_cut > mini)

        total_mask = lt * gt
        flat_data = data_cut[total_mask].flatten()

        if not maxi:
            maxi = np.max(data_cut)
        if not mini:
            mini = np.min(data_cut)
        num_bins = int(self.histogram_pars["nbins"][0])

        n, bins, patches = plt.hist(
            flat_data, num_bins, range=[mini, maxi], normed=False, facecolor='green', alpha=0.5, histtype='bar')
        print("hist with {0} bins".format(num_bins))
        plt.draw()
        plt.show(block=False)
        time.sleep(self.sleep_time)

    def contour_plot(self, x, y, data, fig=None):
        """plot contours in a region around the specified location"""

        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca()
        ax.set_title(self.contour_pars["title"][0])
        ax.set_xlabel(self.contour_pars["xlabel"][0])
        ax.set_ylabel(self.contour_pars["ylabel"][0])

        deltax = np.ceil(self.contour_pars["ncolumns"][0] / 2.)
        deltay = np.ceil(self.contour_pars["nlines"][0] / 2.)
        data_cut = data[y - deltay:y + deltay, x - deltax:x + deltax]

        plt.rcParams['xtick.direction'] = 'out'
        plt.rcParams['ytick.direction'] = 'out'
        ncont = self.contour_pars["ncontours"][0]
        colormap = self.contour_pars["cmap"][0]
        lsty = self.contour_pars["linestyle"][0]

        X, Y = np.meshgrid(np.arange(0, deltax, 0.5) + x - deltax / 2.,
                           np.arange(0, deltay, 0.5) + y - deltay / 2.)  # check this
        plt.contourf(X, Y, data_cut, ncont, alpha=.75, cmap=colormap)
        C = plt.contour(
            X,
            Y,
            data_cut,
            ncont,
            linewidth=.5,
            colors='black',
            linestyle=lsty)
        if self.contour_pars["label"][0]:
            plt.clabel(C, inline=1, fontsize=10, fmt="%5.3f")
        plt.draw()
        plt.show(block=False)
        time.sleep(self.sleep_time)

    def surface_plot(self, x, y, data, fig=None):
        """plot a surface around the specified location

                       "ncolumns":[21,"Number of columns"],
                       "nlines":[21,"Number of lines"],
                       "angh":[-33.,"Horizontal viewing angle in degrees"],
                       "angv":[25.,"Vertical viewing angle in degrees"],
                       "floor":[None,"Minimum value to be contoured"],
                       "ceiling":[None,"Maximum value to be contoured"],
        """

        from mpl_toolkits.mplot3d import Axes3D
        from matplotlib.ticker import LinearLocator, FormatStrFormatter

        if fig is None:
            fig = plt.figure(self._figure_name)
        fig.clf()
        fig.add_subplot(111)
        ax = fig.gca(projection='3d')
        if self.surface_pars["title"][0]:
            ax.set_title(self.surface_pars["title"][0])
        ax.set_xlabel(self.surface_pars["xlabel"][0])
        ax.set_ylabel(self.surface_pars["ylabel"][0])
        if self.surface_pars["zlabel"][0]:
            ax.set_zlabel("Flux")
        fancy = self.surface_pars["fancy"][0]
        deltax = self.surface_pars["ncolumns"][0]
        deltay = self.surface_pars["nlines"][0]

        X = np.arange(x - deltax, x + deltax, 1)
        Y = np.arange(y - deltay, y + deltay, 1)

        X, Y = np.meshgrid(X, Y)
        Z = data[y - deltay:y + deltay, x - deltax:x + deltax]
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
                X, Y, Z, rstride=stride, cstride=stride, cmap=self.surface_pars["cmap"][0], alpha=0.6)
        else:
            surf = ax.plot_surface(X, Y, Z, rstride=stride, cstride=stride, cmap=self.surface_pars[
                                   "cmap"][0], linewidth=0, antialiased=False)

        ax.zaxis.set_major_locator(LinearLocator(10))
        ax.zaxis.set_major_formatter(FormatStrFormatter('%.0f'))
        ax.set_zlim(zmin, zmax)

        if fancy:
            xmin = x - deltax
            ymax = y + deltay
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
        plt.draw()
        plt.show(block=False)
        time.sleep(self.sleep_time)

    def register(self, user_funcs):
        """register a new imexamine function made by the user so that it becomes an option

        Parameters
        ----------
        user_funcs: dict
            Contains a dictionary where each key is the binding for the (function,description) tuple

        Notes
        -----
        The new binding will be added to the dictionary of imexamine functions as long as the key is unique
        The new functions do not have to have default dictionaries associated with them
        imexam_option_funcs = {'a': (self.aper_phot, 'aperture sum, with radius region_size ') ->tuple example

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
                print(
                    "User function: {0:s} added to imexam options with key {1:s}".format(func_name, key))

    @classmethod
    def _add_user_function(cls, func):
        import types
        return setattr(cls, func.__name__, types.MethodType(func, None, cls))

    # Some boilderplate to display matplotlib plots in notebook
    # If QT GUI could interact nicely with --pylab=inline we wouldn't need this

    def showplt(self):
        buf = StringIO.StringIO()
        plt.savefig(buf, bbox_inches=0)
        img = Image(data=bytes(buf.getvalue()),
                    format='png', embed=True)
        buf.close()
        return img

    def set_aperphot_pars(self, user_dict=None):
        """the user may supply a dictionary of par settings"""
        if not user_dict:
            self.aperphot_pars = imexam_defpars.aperphot_pars
        else:
            self.aperphot_pars = user_dict

    def set_radial_pars(self):
        """set parameters for radial profile plots"""

        self.curve_of_growth_pars = imexam_defpars.curve_of_growth_pars

    def set_surface_pars(self):
        """set parameters for surface plots"""

        self.surface_pars = imexam_defpars.surface_pars

    def set_line_fit_pars(self):
        """set parameters for 1D line fit plots"""

        self.line_fit_pars = imexam_defpars.line_fit_pars

    def set_column_fit_pars(self):
        """set parameters for 1D line fit plots"""

        self.column_fit_pars = imexam_defpars.column_fit_pars

    def set_contour_pars(self):
        """set parameters for contour plots"""

        self.contour_pars = imexam_defpars.contour_pars

    def set_histogram_pars(self):
        """set parameters for histogram plots"""

        self.histogram_pars = imexam_defpars.histogram_pars

    def set_lineplot_pars(self):
        """set parameters for line plots"""

        self.lineplot_pars = imexam_defpars.lineplot_pars

    def set_colplot_pars(self):
        """set parameters for column plots"""

        self.colplot_pars = imexam_defpars.colplot_pars

    def set_histogram_pars(self):
        """set parameters for histogram plots"""

        self.histogram_pars = imexam_defpars.histogram_pars

    def set_contour_pars(self):
        """set parameters for histogram plots"""

        self.contour_pars = imexam_defpars.contour_pars

    def reset_defpars(self):
        """set all pars to their defaults"""
        self._define_pars()
