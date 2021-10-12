# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""Functions to help enable math and fitting in the main examine code"""

import numpy as np
import warnings

from astropy.modeling import models, fitting
from astropy.stats import gaussian_sigma_to_fwhm, sigma_clip


def gfwhm(sigmax, sigmay=None):
    """Compute the Gaussian full width half max.

    Parameters
    ----------

    sigmax: float
        The input sigma to use

    sigmay: float
        The input sigma to use

    Returns
    -------
    The FWHM tuple for the Gaussian

    """
    if sigmax is None:
        print("Need at least one sigma value for Gaussian FWHM")
        return (None, None)

    fwhmx = gaussian_sigma_to_fwhm * sigmax
    if sigmay is None:
        fwhmy = fwhmx
    else:
        fwhmy = gaussian_sigma_to_fwhm * sigmay

    return (fwhmx, fwhmy)


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
        print("Need alpha AND gamma values for moffat FWHM")
        return None

    return 2 * alpha * np.sqrt(2 ** (1 / gamma) - 1)


def fit_moffat_1d(data, gamma=2., alpha=1., sigma_factor=0.,
                  center_at=None, weighted=False):
    """Fit a 1D moffat profile to the data and return the fit.

    Parameters
    ----------
    data: 2D data array
        The input sigma to use
    gamma: float (optional)
        The input gamma to use
    alpha: float (optional)
        The input alpha to use
    sigma_factor: float (optional)
        If sigma>0 then sigma clipping of the data is performed
        at that level
    center_at: float or None
        None by default, set to value to use as center
    weighted: bool
        if weighted is True, then weight the values by basic
        uncertainty hueristic

    Returns
    -------
    The fitted 1D moffat model for the data

    """
    # data is assumed to already be chunked to a reasonable size
    ldata = len(data)

    # guesstimate mean
    if center_at:
        x0 = 0
    else:
        x0 = int(ldata / 2.)

    # assumes negligable background
    if weighted:
        z = np.nan_to_num(1. / np.sqrt(data))  # use as weight

    x = np.arange(ldata)

    # Initialize the fitter
    fitter = fitting.LevMarLSQFitter()
    if sigma_factor > 0:
        fit = fitting.FittingWithOutlierRemoval(fitter,
                                                sigma_clip,
                                                niter=3,
                                                sigma=sigma_factor)
    else:
        fit = fitter

    # Moffat1D + constant
    model = (models.Moffat1D(amplitude=max(data),
                             x_0=x0,
                             gamma=gamma,
                             alpha=alpha) +
             models.Polynomial1D(c0=data.min(), degree=0))

    with warnings.catch_warnings():
        # Ignore model linearity warning from the fitter
        warnings.simplefilter('ignore')
        if weighted:
            results = fit(model, x, data, weights=z)
        else:
            results = fit(model, x, data)

    # previous yield amp, ycenter, xcenter, sigma, offset
    # if sigma clipping is used, results is a tuple of data, model
    if sigma_factor > 0:
        return results[1]
    else:
        return results


def fit_gauss_1d(radius, flux, sigma_factor=0, center_at=None, weighted=False):
    """Fit a 1D gaussian to the data and return the fit.

    Parameters
    ----------
    radius: array of float
        set center_at and the center will be taken there
    flux: array of float
        values should correspond to radius array
    sigma_factor: float (optional)
        If sigma>0 then sigma clipping of the data is performed
        at that level
    center_at: float or None
        None by default, set to value to use as center
        If the value is None, center will be set at half the
        array size.
    weighted: bool
        if weighted is True, then weight the values by basic
        uncertainty hueristic

    Returns
    -------
    The fitted 1D gaussian model for the data.
    """

    if radius.shape != flux.shape:
        raise ValueError("Expected same sizes for radius and flux")

    # guesstimate the mean
    # assumes ordered radius
    if center_at is None:
        delta = int(len(radius) / 2.)
    else:
        delta = center_at

    # assumes negligable background
    if weighted:
        z = np.nan_to_num(np.log(flux))

    # Initialize the fitter
    fitter = fitting.LevMarLSQFitter()
    if sigma_factor > 0:
        fit = fitting.FittingWithOutlierRemoval(fitter,
                                                sigma_clip,
                                                niter=3,
                                                sigma=sigma_factor)
    else:
        fit = fitter

    # Gaussian1D + a constant
    model = (models.Gaussian1D(amplitude=flux.max() - flux.min(),
                               mean=delta, stddev=1.) +
             models.Polynomial1D(c0=flux.min(), degree=0))

    with warnings.catch_warnings():
        # Ignore model linearity warning from the fitter
        warnings.simplefilter('ignore')
        if weighted:
            results = fit(model, radius, flux, weights=z)
        else:
            results = fit(model, radius, flux)

    # previous yield amp, ycenter, xcenter, sigma, offset
    # if sigma clipping is used, results is a tuple of data, model
    if sigma_factor > 0:
        return results[1]
    else:
        return results


def fit_gaussian_2d(data, sigma=3., theta=0., sigma_factor=0):
    """center the data  by fitting a 2d gaussian to the region.

    Parameters
    ----------

    data: 2D float array
        should be a 2d array, the initial center is used to estimate
        the fit center
    sigma: float (optional)
        The sigma value for the starting gaussian model
    theta: float(optional)
        The theta value for the starting gaussian model
    sigma_factor: float (optional)
        If sigma_factor > 0 then clipping will be performed
        on the data during the model fit

    Returns
    -------
    The full gaussian fit model, from which the center can be extracted

    """
    # use a smaller bounding box so that we are only fitting the local data
    delta = int(len(data) / 2)  # guess the center
    amp = data.max() - data.min()  # guess the amplitude
    ldata = len(data)
    yy, xx = np.mgrid[:ldata, :ldata]

    # Initialize the fitter
    fitter = fitting.LevMarLSQFitter()
    if sigma_factor > 0:
        fit = fitting.FittingWithOutlierRemoval(fitter,
                                                sigma_clip,
                                                niter=3,
                                                sigma=sigma_factor)
    else:
        fit = fitter

    # Gaussian2D(amp,xmean,ymean,xstd,ystd,theta) + a constant
    model = (models.Gaussian2D(amp, delta, delta, sigma, sigma, theta) +
             models.Polynomial2D(c0_0=data.min(), degree=0))
    with warnings.catch_warnings():
        # Ignore model linearity warning from the fitter
        warnings.simplefilter('ignore')
        results = fit(model, xx, yy, data)

    # previous yield amp, ycenter, xcenter, sigma, offset
    # if sigma clipping is used, results is a tuple of data, model
    if sigma_factor > 0:
        return results[1]
    else:
        return results


def fit_mex_hat_1d(data, sigma_factor=0, center_at=None, weighted=False):
    """Fit a 1D Mexican Hat function to the data.

    Parameters
    ----------

    data: 2D float array
        should be a 2d array, the initial center is used to estimate
        the fit center
    sigma_factor: float (optional)
        If sigma_factor > 0 then clipping will be performed
        on the data during the model fit
    center_at: float or None
        None by default, set to value to use as center
    weighted: bool
        if weighted is True, then weight the values by basic
        uncertainty hueristic

    Returns
    -------
    The the fit model for mexican hat 1D function
    """
    ldata = len(data)
    if center_at:
        x0 = 0
    else:
        x0 = int(ldata / 2.)

    # assumes negligable background
    if weighted:
        z = np.nan_to_num(1. / np.sqrt(data))  # use as weight

    x = np.arange(ldata)
    fixed_pars = {"x_0": True}

    # Initialize the fitter
    fitter = fitting.LevMarLSQFitter()
    if sigma_factor > 0:
        fit = fitting.FittingWithOutlierRemoval(fitter,
                                                sigma_clip,
                                                niter=3,
                                                sigma=sigma_factor)
    else:
        fit = fitter

    # Mexican Hat 1D + constant
    model = (models.MexicanHat1D(amplitude=np.max(data),
                                 x_0=x0,
                                 sigma=2.,
                                 fixed=fixed_pars) +
             models.Polynomial1D(c0=data.min(), degree=0))

    with warnings.catch_warnings():
        # Ignore model linearity warning from the fitter
        warnings.simplefilter('ignore')
        if weighted:
            results = fit(model, x, data, weights=z)
        else:
            results = fit(model, x, data)

    # previous yield amp, ycenter, xcenter, sigma, offset
    if sigma_factor > 0:
        return results[1]
    else:
        return results


def fit_airy_2d(data, x=None, y=None, sigma_factor=0):
    """Fit an AiryDisk2D model to the data.

    Parameters
    ----------

    data: 2D float array
        should be a 2d array, the initial center is used to estimate
        the fit center
    x: float (optional)
        xcenter location
    y: float (optional)
        ycenter location
    sigma_factor: float (optional)
        If sigma_factor > 0 then clipping will be performed
        on the data during the model fit

    Returns
    -------
    The the fit model for Airy2D function

    """
    delta = int(len(data) / 2)  # guess the center
    ldata = len(data)

    if x is None:
        x = delta
    if y is None:
        y = delta
    fixed_pars = {"x_0": True, "y_0": True}  # hold these constant
    yy, xx = np.mgrid[:ldata, :ldata]

    # Initialize the fitter
    fitter = fitting.LevMarLSQFitter()
    if sigma_factor > 0:
        fit = fitting.FittingWithOutlierRemoval(fitter,
                                                sigma_clip,
                                                niter=3,
                                                sigma=sigma_factor)
    else:
        fit = fitter

    # AiryDisk2D(amplitude, x_0, y_0, radius) + constant
    model = (models.AiryDisk2D(np.max(data),
                               x_0=x,
                               y_0=y,
                               radius=delta,
                               fixed=fixed_pars) +
             models.Polynomial2D(c0_0=data.min(), degree=0))
    with warnings.catch_warnings():
        # Ignore model warnings for new_plot_window
        warnings.simplefilter('ignore')
        results = fit(model, xx, yy, data)

    if sigma_factor > 0:
        return results[1]
    else:
        return results


def fit_poly_n(data, deg=1, sigma_factor=0):
    """Fit a Polynomial 1D model to the data.

    Parameters
    ----------

    data: float array
        should be a 1d or 2d array
    deg: int
        The degree of polynomial to fit
    sigma_factor: float (optional)
        If sigma_factor > 0 then clipping will be performed
        on the data during the model fit

    Returns
    -------
    The the polynomial fit model for the function
    """
    if len(data) < deg + 1:
        raise ValueError("fit_poly_n: Need more data for fit")

    # define the model
    poly = models.Polynomial1D(deg)

    # set the axis range for fitting
    ax = np.arange(len(data))

    # define the fitter
    fitter = fitting.LinearLSQFitter()

    if sigma_factor > 0:
        fit = fitting.FittingWithOutlierRemoval(fitter,
                                                sigma_clip,
                                                sigma=sigma_factor,
                                                niter=3)
    else:
        fit = fitter

    try:
        result = fit(poly, ax, data)
    except ValueError:
        result = None

    if sigma_factor > 0:
        result = result[1]

    return result
