# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""help with math functions
   From iraf documentation:

            The intensity profile functions (with unit peak) are:

                I(r) = exp (-0.5 * (r/sigma)**2)                    Gaussian
                I(r) = (1 + (r/alpha)**2)) ** (-beta)               Moffat

            with parameters sigma, alpha, and  beta.   The  normalized  enclosed
            flux profiles, which is what is actually fit, are then:

                F(r) = 1 - exp (-0.5 * (r/sigma)**2)                Gaussian
                F(r) = 1 - (1 + (r/alpha)**2)) ** (1-beta)          Moffat

            The  fits  determine  the  parameters  sigma or alpha and beta (if a
            beta value is not specified by the users).  The reported FWHM values
            are given by:

                GFWHM = 2 * sigma * sqrt (2 * ln (2))               Gaussian
                MFWHM = 2 * alpha * sqrt (2 ** (1/beta) - 1)        Moffat

            were the units are adjusted by the pixel scale factor.

            In  addition  to  the  four  size  measurements  there  are  several
            additional quantities which are determined.  Other quantities  which
            are  computed  are the relative magnitude, ellipticity, and position
            angle.  The magnitude of an individual measurement is obtained  from
            the   maximum   flux   attained   in   the   enclosed  flux  profile
            computation.   Though  the  normalization  and  background  may   be
            adjusted  interactively later, the magnitude is not changed from the
            initial determination.  The relative magnitude of an object is  then
            computed as

                rel. mag. = -2.5 * log (object flux / maximum star flux)

            The  maximum star magnitude over all stars is used as the zero point
            for the relative magnitudes (hence it is possible for an  individual
            object relative magnitude to be less than zero).

            The  ellipticity  and positional angle of an object are derived from
            the second central intensity weighted moments.  The moments are:


                    Mxx = sum { (I - B) * x * x } / sum { I - B }
                    Myy = sum { (I - B) * y * y } / sum { I - B }
                    Mxy = sum { (I - B) * x * y } / sum { I - B }

            where x and y are the distances from the object  center,  I  is  the
            pixel  intensity and B is the background intensity.  The sum is over
            the same  subpixels  used  in  the  enclosed  flux  evaluation  with
            intensities   above   an   isophote  which  is  slightly  above  the
            background.  The ellipticity and position angles  are  derived  from
            the moments by the equations:

                    M1 = (Mxx - Myy) / (Mxx + Myy)
                    M2 = 2 * Mxy / (Mxx + Myy)
                    ellip = (M1**2 + M2**2) ** 1/2
                    pa = atan (M2 / M1) / 2

            where  ** is the exponentiation operator and atan is the arc tangent
            operator.  The ellipticity is essentially (a - b) / (a + b) where  a
            is  a major axis scale length and b is a minor axis scale length.  A
            value of zero corresponds to a circular image.  The  position  angle
            is given in degrees counterclockwise from the x or column axis.

            One of the quantities computed for the  graphical  analysis  is  the
            FWHM  of a Gaussian or Moffat profile that encloses the same flux as
            the measured object as a function of the level.  The equation are:

               FWHM = 2 * r(level) * sqrt (ln(2.) / ln (1/(1-level)))  Gaussian

               FWHM = 2 * r(level) * sqrt (2**(1/beta)-1) /
                      sqrt ((1-level)**(1/(1-beta))-1)                 Moffat

            where r(level) is the radius that encloses "level" fraction  of  the
            total  flux.   ln  is  the  natural logarithm and sqrt is the square
            root.  The beta value is either the  user  specified  value  or  the
            value determined by fitting the enclosed flux profile.

            This  function  of  level  will  be a constant if the object profile
            matches the Gaussian or Moffat profile.  Deviations from a  constant
            show  the  departures  from  the  profile model.  The Moffat profile
            used in making the graphs except for the  case  where  the  size  is
            GFWHM.


"""

from __future__ import print_function, division

import numpy as np
from scipy.optimize import curve_fit


def exponential(x, a, b, c):
    """exponential function"""
    return a * np.exp(-b * x) - c


def gaussian(x, a, mu, sigma, b=0):
    """Functional form for the gaussian 1D function

    Parameters
    ----------
    x: float
        is the data
    a: float
        is amplitude, the max value of the fitted PSF and value at the centroid coordinates
    mu: float
        is the mean
    sigma: float
        is the standard dev

    b: float
        is the average local background

    """
    return b + a * np.exp(-(x - mu) ** 2 / (2. * sigma ** 2))


def gfwhm(sigma):
    """Compute the gaussian full width half max

    Parameters
    ----------

    sigma: float
        The input sigma to use

    Returns
    -------
    The value of the FWHM for the gaussian

    """
    return 2. * sigma * np.sqrt(2. * np.log(2.))


def moffat(x, alpha, beta, mu, sigma, b=0):
    """Functional form for a 1D Moffat profile

    Parameters
    ----------
    x: float
        the data

    alpha: float
        the possible seeing for the psf

    beta: float
        controls the overall shape of the fitting function, when beta=1 it's a lorentzian

    b: float
        The average local background
    mu: float
        The mean


    See Also
    --------
    http://en.wikipedia.org/wiki/Moffat_distribution

    """
    return b + alpha / (((x - mu) ** 2 / sigma ** 2 + 1) ** (1 - beta))


def mfwhm(alpha, beta):
    """compute the <offat full width half max

    Returns
    -------
    The value of the FWHM for the Moffat profile with give alpha and beta

    """
    return 2. * alpha * np.sqrt(2 ** (1. / beta) - 1.)


def gauss_center(data):
    """center the data  by fitting a 2d gaussian to the region

    Parameters
    ----------

    data: float
        should be a 2d array, the initial center is used to estimate the fit center


    """

    # use a smaller bounding box so that we are only fitting the local data
    delta = int(len(data) / 2)
    guess2dc = (1., delta, delta, 3., 0.)

    xx = np.linspace(0, len(data), len(data))
    yy = np.linspace(0, len(data), len(data))
    popt, pcov = curve_fit(
        gaussian2dc, np.meshgrid(
            xx, yy), data.flatten(), p0=guess2dc)
    return popt


def gaussian2dc(point, amp, xo, yo, sigma, offset):
    """Functional definition for a circular 2D gaussian function

    Parameters
    ----------
    point: (y,x) float array
        The values at x,y
    xo: float
        The mean for x

    yo: float
        The mean for y

    Notes
    -----
    sigmax=sigmay=circular otherwise elliptical

    See Also
    --------
    http://en.wikipedia.org/wiki/Gaussian_function
    """
    y, x = point
    xo = float(xo)
    yo = float(yo)

    a = 1 / (2 * sigma ** 2)
    b = 0
    c = 1 / (2 * sigma ** 2)
    result = offset + amp * \
        np.exp(-(a * ((x - xo) ** 2) + c * ((y - yo) ** 2)))
    return result.ravel()


def gaussian2de(point, amp, xo, yo, sigmax, sigmay, theta, offset):
    """Functional definition for the 2D elliptical gaussian function

    Parameters
    ----------
    point: (y,x) float array
        the values at x,y

    xo: float
        mean for x

    yo: float
        mean for y

    Notes
    -----
    sigmax=sigmay=circular otherwise elliptical

    See Also
    --------
    http://en.wikipedia.org/wiki/Gaussian_function
    """
    y, x = point
    xo = float(xo)
    yo = float(yo)

    a = (np.cos(theta) ** 2) / (2 * sigmax ** 2) + \
        (np.sin(theta) ** 2) / (2 * sigmay ** 2)
    b = -(np.sin(2 * theta)) / (4 * sigmax ** 2) + \
        (np.sin(2 * theta)) / (4 * sigmay ** 2)
    c = (np.sin(theta) ** 2) / (2 * sigmax ** 2) + \
        (np.cos(theta) ** 2) / (2 * sigmay ** 2)
    result = offset + amp * \
        np.exp(-(a * ((x - xo) ** 2) + 2 * b * (x - xo)
                 * (y - yo) + c * ((y - yo) ** 2)))
    return result.ravel()
