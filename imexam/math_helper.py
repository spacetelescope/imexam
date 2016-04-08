# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""Functions to help enable math and fitting in the main examine code"""

from __future__ import print_function, division

import numpy as np
import warnings
from astropy.modeling import models, fitting
from astropy.modeling.models import custom_model


@custom_model
def sum_of_gaussians(x, amplitude1=1., mean1=-1., sigma1=1.,
                     amplitude2=1., mean2=1., sigma2=1.):
    """Custom astropy model for the sum of 2 gaussians."""
    return (amplitude1 * np.exp(-0.5 * ((x - mean1) / sigma1)**2) +
            amplitude2 * np.exp(-0.5 * ((x - mean2) / sigma2)**2))


@custom_model
def exponential(x, a, b, c):
    """Custom astropy model for an exponential function."""
    return a * np.exp(-b * x) - c


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

    # Gaussian1D
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
