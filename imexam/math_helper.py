# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""Functions to help enable math and fitting in the main examine code"""

from __future__ import print_function, division

import numpy as np
import warnings
from astropy.modeling import models, fitting




def gfwhm(sigmax, sigmay=None):
    """Compute the gaussian full width half max.

    Parameters
    ----------

    sigmax: float
        The input sigma to use

    sigmay: float
        The input sigma to use

    Returns
    -------
    The FWHM tuple for the gaussian

    """
    if sigmax is None:
        print("Need at least one sigma value")
        return (None, None)

    g = lambda x: x * np.sqrt(8.0 * np.log(2.))

    if sigmay is None:
        return (g(sigmax), g(sigmax))  # assume circular where sigmax = sigmay
    else:
        return (g(sigmax), g(sigmay))


def mfwhm(alpha=0, gamma=0):
    """Compute the Moffat full width half max.

    Parameters
    ----------

    sigmax: float
        The input sigma to use

    sigmay: float
        The input sigma to use

    Returns
    -------
    The FWHM tuple for a Moffat function
    fwhm = 2* alpha * sqrt(2^(1/gamma) -1 ))
    """
    if alpha == 0 or gamma == 0:
        print("Need alpha AND gamma values")
        return None

    g = lambda x, y: 2 * x * np.sqrt(2 ** (1/y) - 1)

    return g(alpha, gamma)


def fit_moffat_1d(data, gamma=2., alpha=1.):
    """Fit a 1D moffat profile to the data and return the fit."""
    # data is assumed to already be chunked to a reasonable size
    ldata = len(data)
    x = np.arange(ldata)

    # Fit model to data
    fit = fitting.LevMarLSQFitter()

    # Moffat1D
    model = models.Moffat1D(amplitude=max(data), x_0=ldata/2, gamma=gamma, alpha=alpha)
    with warnings.catch_warnings():
        # Ignore model linearity warning from the fitter
        warnings.simplefilter('ignore')
        results = fit(model, x, data)

    # previous yield amp, ycenter, xcenter, sigma, offset
    return results


def fit_gauss_1d(data):
    """Fit a 1D gaussian to the data and return the fit."""
    # data is assumed to already be chunked to a reasonable size
    ldata = len(data)
    x = np.arange(ldata)

    # Fit model to data
    fit = fitting.LevMarLSQFitter()

    # Gaussian1D
    model = models.Gaussian1D(amplitude=1, mean=0, stddev=1.)
    with warnings.catch_warnings():
        # Ignore model linearity warning from the fitter
        warnings.simplefilter('ignore')
        results = fit(model, x, data)

    # previous yield amp, ycenter, xcenter, sigma, offset
    return results


def gauss_center(data, sigma=3., theta=0.):
    """center the data  by fitting a 2d gaussian to the region.

    Parameters
    ----------

    data: float
        should be a 2d array, the initial center is used to estimate
        the fit center
    """
    # use a smaller bounding box so that we are only fitting the local data
    delta = int(len(data) / 2)  # guess the center
    ldata = len(data)
    yy, xx = np.mgrid[:ldata, :ldata]

    # Fit model to data
    fit = fitting.LevMarLSQFitter()

    # Gaussian2D(amp,xmean,ymean,xstd,ystd,theta)
    model = models.Gaussian2D(1, delta, delta, sigma, sigma, theta)
    with warnings.catch_warnings():
        # Ignore model linearity warning from the fitter
        warnings.simplefilter('ignore')
        results = fit(model, xx, yy, data)

    # previous yield amp, ycenter, xcenter, sigma, offset
    return results


def fit_mex_hat_1d(data):
    """Fit a 1D Mexican Hat function to the data."""
    ldata = len(data)
    x = np.arange(ldata)
    fixed_pars = {"x_0": True}

    # Fit model to data
    fit = fitting.LevMarLSQFitter()

    # Mexican Hat 1D
    model = models.MexicanHat1D(amplitude=np.max(data),
                                x_0=ldata/2, sigma=2., fixed=fixed_pars)
    with warnings.catch_warnings():
        # Ignore model linearity warning from the fitter
        warnings.simplefilter('ignore')
        results = fit(model, x, data)

    # previous yield amp, ycenter, xcenter, sigma, offset
    return results


def fit_airy_2d(data, x=None, y=None):
    """Fit an AiryDisk2D model to the data."""
    delta = int(len(data) / 2)  # guess the center
    ldata = len(data)

    if not x:
        x = delta
    if not y:
        y = delta
    fixed_pars = {"x_0": True, "y_0": True}  # hold these constant
    yy, xx = np.mgrid[:ldata, :ldata]

    # fit model to the data
    fit = fitting.LevMarLSQFitter()

    # AiryDisk2D(amplitude, x_0, y_0, radius)
    model = models.AiryDisk2D(np.max(data), x_0=x, y_0=y, radius=delta,
                              fixed=fixed_pars)
    with warnings.catch_warnings():
            # Ignore model warnings for new_plot_window
            warnings.simplefilter('ignore')
            results = fit(model, xx, yy, data)

    return results


def fit_poly_n(data, x=None, y=None, deg=1):
    """Fit a Polynomial 1D model to the data."""

    # define the model
    poly = models.Polynomial1D(deg)

    # set the axis range for fitting
    ax = np.arange(len(data))

    # define the fitter
    fit = fitting.LinearLSQFitter()
    try:
        result = fit(poly, ax, data)
    except:
        ValueError
        result = None
    return result
