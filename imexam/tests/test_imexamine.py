"""Licensed under a 3-clause BSD style license - see LICENSE.rst.

Make sure that the basic plots in imexamine are working as expected.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import pytest
import numpy as np
from numpy.testing import assert_allclose, assert_equal, assert_array_equal
from imexam.imexamine import Imexamine

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import photutils
    HAS_PHOTUTILS = True
except ImportError:
    HAS_PHOTUTILS = False


# make some data to test with
test_data = np.zeros((100, 100), dtype=np.float)
test_data[25:75, 25:75] = 1.0
test_data[35:65, 35:65] = 2.0
test_data[45:55, 45:55] = 3.0


@pytest.mark.skipif('not HAS_MATPLOTLIB')
def test_column_plot():
    """Check the column plot function."""
    plots = Imexamine()
    plots.set_data(test_data)
    plots.plot_column(50, 50)
    f = plt.gca()
    xplot, yplot = f.lines[0].get_xydata().T
    assert_equal(yplot, test_data[50, :])
    plt.close()


@pytest.mark.skipif('not HAS_MATPLOTLIB')
def test_line_plot():
    """check the line plot function."""
    plots = Imexamine()
    plots.set_data(test_data)
    plots.plot_line(50, 50)
    f = plt.gca()
    xplot, yplot = f.lines[0].get_xydata().T
    assert_equal(yplot, test_data[:, 50])
    plt.close()


@pytest.mark.skipif('not HAS_PHOTUTILS')
def test_aper_phot(capsys):
    """Check that apertures are as expected from photutils"""
    apertures = photutils.CircularAperture((50, 50), 5)
    aperture_area = apertures.area()
    assert_equal(aperture_area, 78.53981633974483)
    rawflux_table = photutils.aperture_photometry(
        test_data,
        apertures,
        subpixels=1,
        method="center")
    total_flux = float(rawflux_table['aperture_sum'][0])
    assert_equal(total_flux, 207.)


def test_line_fit():
    """Fit a Gaussian1D line to the data."""
    plots = Imexamine()
    plots.set_data(test_data)
    fit = plots.line_fit(50, 50, form='Gaussian1D', genplot=False)
    amp = 2.8152269683542137
    mean = 49.45671107821953
    stddev = 13.051081779478146

    assert_allclose(amp, fit.amplitude, 1e-6)
    assert_allclose(mean, fit.mean, 1e-6)
    assert_allclose(stddev, fit.stddev, 1e-6)


def test_column_fit():
    """Fit a Gaussian1D column to the data."""
    plots = Imexamine()
    plots.set_data(test_data)
    fit = plots.column_fit(50, 50, form='Gaussian1D', genplot=False)
    amp = 2.8285560281694115
    mean = 49.42625526973088
    stddev = 12.791137635400535

    assert_allclose(amp, fit.amplitude, 1e-6)
    assert_allclose(mean, fit.mean, 1e-6)
    assert_allclose(stddev, fit.stddev, 1e-6)


def test_gauss_center():
    """Check the gaussian center fitting."""
    # make a 2d dataset with a gaussian at the center
    from astropy.convolution import Gaussian2DKernel
    gaussian_2D_kernel = Gaussian2DKernel(10)
    plots = Imexamine()
    plots.set_data(gaussian_2D_kernel.array)
    a, xx, yy, xs, ys = plots.gauss_center(37, 37)

    amp = 0.0015915494309189533
    xc = 40.0
    yc = 40.0
    xsig = 10.0
    ysig = 10.0

    assert_allclose(amp, a, 1e-6)
    assert_allclose(xc, xx, 1e-4)
    assert_allclose(yc, yy, 1e-4)
    assert_allclose(xsig, xs, 0.01)
    assert_allclose(ysig, ys, 0.01)


def test_radial_profile():
    """Test the radial profile function without background subtraction"""
    from astropy.convolution import Gaussian2DKernel
    data = Gaussian2DKernel(1.5, x_size=25, y_size=25)
    plots = Imexamine()
    plots.set_data(data.array)
    # check the binned results
    plots.radial_profile_pars['pixels'][0] = False
    x, y = plots.radial_profile(12, 12, genplot=False)

    rad = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    flux = [4.53542348e-02,   3.00703719e-01,   3.54889792e-01,
            1.95806071e-01,   7.56662018e-02,   2.46976310e-02,
            2.54073324e-03,   1.51802506e-04,   1.08323362e-06,
            3.65945812e-10]

    assert_array_equal(rad, x)
    assert_allclose(flux, y, 1e-7)


@pytest.mark.skipif('not HAS_PHOTUTILS')
def test_radial_profile_background():
    """Test the radial profile function with background subtraction"""
    from astropy.convolution import Gaussian2DKernel
    data = Gaussian2DKernel(1.5, x_size=25, y_size=25)
    plots = Imexamine()
    plots.set_data(data.array)
    # check the binned results
    plots.radial_profile_pars['pixels'][0] = False
    plots.radial_profile_pars['background'][0] = True
    x, y = plots.radial_profile(12, 12, genplot=False)

    rad = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    flux = [4.535423e-02, 3.007037e-01, 3.548898e-01, 1.958061e-01,
            7.566620e-02, 2.469763e-02, 2.540733e-03, 1.518025e-04,
            1.083221e-06, 3.605551e-10]

    assert_array_equal(rad, x)
    assert_allclose(flux, y, 1e-6)


def test_radial_profile_pixels():
    """Test the radial profile function without background subtraction"""
    from astropy.convolution import Gaussian2DKernel
    data = Gaussian2DKernel(1.5, x_size=25, y_size=25)
    plots = Imexamine()
    plots.set_data(data.array)
    # check the unbinned results
    plots.radial_profile_pars['pixels'][0] = True
    x, y = plots.radial_profile(12, 12, genplot=False)

    rad = [1.00485917e-14,   1.00000000e+00,   1.00000000e+00,
           1.00000000e+00,   1.00000000e+00,   1.41421356e+00,
           1.41421356e+00,   1.41421356e+00,   1.41421356e+00,
           2.00000000e+00,   2.00000000e+00,   2.00000000e+00,
           2.00000000e+00,   2.23606798e+00,   2.23606798e+00,
           2.23606798e+00,   2.23606798e+00,   2.23606798e+00,
           2.23606798e+00,   2.23606798e+00,   2.23606798e+00,
           2.82842712e+00,   2.82842712e+00,   2.82842712e+00,
           2.82842712e+00,   3.00000000e+00,   3.00000000e+00,
           3.00000000e+00,   3.00000000e+00,   3.16227766e+00,
           3.16227766e+00,   3.16227766e+00,   3.16227766e+00,
           3.16227766e+00,   3.16227766e+00,   3.16227766e+00,
           3.16227766e+00,   3.60555128e+00,   3.60555128e+00,
           3.60555128e+00,   3.60555128e+00,   3.60555128e+00,
           3.60555128e+00,   3.60555128e+00,   3.60555128e+00,
           4.00000000e+00,   4.00000000e+00,   4.00000000e+00,
           4.00000000e+00,   4.12310563e+00,   4.12310563e+00,
           4.12310563e+00,   4.12310563e+00,   4.12310563e+00,
           4.12310563e+00,   4.12310563e+00,   4.12310563e+00,
           4.24264069e+00,   4.24264069e+00,   4.24264069e+00,
           4.24264069e+00,   4.47213595e+00,   4.47213595e+00,
           4.47213595e+00,   4.47213595e+00,   4.47213595e+00,
           4.47213595e+00,   4.47213595e+00,   4.47213595e+00,
           5.00000000e+00,   5.00000000e+00,   5.00000000e+00,
           5.00000000e+00,   5.00000000e+00,   5.00000000e+00,
           5.00000000e+00,   5.00000000e+00,   5.00000000e+00,
           5.00000000e+00,   5.00000000e+00,   5.00000000e+00,
           5.09901951e+00,   5.09901951e+00,   5.09901951e+00,
           5.09901951e+00,   5.09901951e+00,   5.09901951e+00,
           5.09901951e+00,   5.09901951e+00,   5.38516481e+00,
           5.38516481e+00,   5.38516481e+00,   5.38516481e+00,
           5.38516481e+00,   5.38516481e+00,   5.38516481e+00,
           5.38516481e+00,   5.65685425e+00,   5.65685425e+00,
           5.65685425e+00,   5.65685425e+00,   5.83095189e+00,
           5.83095189e+00,   5.83095189e+00,   5.83095189e+00,
           5.83095189e+00,   5.83095189e+00,   5.83095189e+00,
           5.83095189e+00,   6.00000000e+00,   6.00000000e+00,
           6.00000000e+00,   6.00000000e+00,   6.08276253e+00,
           6.08276253e+00,   6.08276253e+00,   6.08276253e+00,
           6.08276253e+00,   6.08276253e+00,   6.08276253e+00,
           6.08276253e+00,   6.32455532e+00,   6.32455532e+00,
           6.32455532e+00,   6.32455532e+00,   6.32455532e+00,
           6.32455532e+00,   6.32455532e+00,   6.32455532e+00,
           6.40312424e+00,   6.40312424e+00,   6.40312424e+00,
           6.40312424e+00,   6.40312424e+00,   6.40312424e+00,
           6.40312424e+00,   6.40312424e+00,   6.70820393e+00,
           6.70820393e+00,   6.70820393e+00,   6.70820393e+00,
           6.70820393e+00,   6.70820393e+00,   6.70820393e+00,
           6.70820393e+00,   7.00000000e+00,   7.00000000e+00,
           7.07106781e+00,   7.07106781e+00,   7.07106781e+00,
           7.07106781e+00,   7.07106781e+00,   7.07106781e+00,
           7.07106781e+00,   7.07106781e+00,   7.21110255e+00,
           7.21110255e+00,   7.21110255e+00,   7.21110255e+00,
           7.21110255e+00,   7.21110255e+00,   7.21110255e+00,
           7.21110255e+00,   7.28010989e+00,   7.28010989e+00,
           7.28010989e+00,   7.28010989e+00,   7.61577311e+00,
           7.61577311e+00,   7.61577311e+00,   7.61577311e+00,
           7.81024968e+00,   7.81024968e+00,   7.81024968e+00,
           7.81024968e+00,   7.81024968e+00,   7.81024968e+00,
           7.81024968e+00,   7.81024968e+00,   8.06225775e+00,
           8.06225775e+00,   8.06225775e+00,   8.06225775e+00,
           8.48528137e+00,   8.48528137e+00,   8.48528137e+00,
           8.48528137e+00,   8.60232527e+00,   8.60232527e+00,
           8.60232527e+00,   8.60232527e+00,   9.21954446e+00,
           9.21954446e+00,   9.21954446e+00,   9.21954446e+00,
           9.89949494e+00]

    flux = [1.19552465e-02,   2.32856406e-02,   2.32856406e-02,
            3.93558331e-03,   3.93558331e-03,   4.53542348e-02,
            7.66546959e-03,   7.66546959e-03,   1.29556643e-03,
            2.90802459e-02,   2.90802459e-02,   8.30691786e-04,
            8.30691786e-04,   5.66405848e-02,   5.66405848e-02,
            9.57301302e-03,   9.57301302e-03,   1.61796667e-03,
            1.61796667e-03,   2.73457911e-04,   2.73457911e-04,
            7.07355303e-02,   2.02059585e-03,   2.02059585e-03,
            5.77193322e-05,   2.32856406e-02,   2.32856406e-02,
            1.12421908e-04,   1.12421908e-04,   4.53542348e-02,
            4.53542348e-02,   7.66546959e-03,   7.66546959e-03,
            2.18967977e-04,   2.18967977e-04,   3.70085038e-05,
            3.70085038e-05,   5.66405848e-02,   5.66405848e-02,
            1.61796667e-03,   1.61796667e-03,   2.73457911e-04,
            2.73457911e-04,   7.81146217e-06,   7.81146217e-06,
            1.19552465e-02,   1.19552465e-02,   9.75533570e-06,
            9.75533570e-06,   2.32856406e-02,   2.32856406e-02,
            3.93558331e-03,   3.93558331e-03,   1.90007994e-05,
            1.90007994e-05,   3.21138811e-06,   3.21138811e-06,
            4.53542348e-02,   2.18967977e-04,   2.18967977e-04,
            1.05716645e-06,   2.90802459e-02,   2.90802459e-02,
            8.30691786e-04,   8.30691786e-04,   2.37291269e-05,
            2.37291269e-05,   6.77834392e-07,   6.77834392e-07,
            2.32856406e-02,   2.32856406e-02,   3.93558331e-03,
            3.93558331e-03,   1.12421908e-04,   1.12421908e-04,
            1.90007994e-05,   1.90007994e-05,   5.42767351e-07,
            5.42767351e-07,   9.17349095e-08,   9.17349095e-08,
            7.66546959e-03,   7.66546959e-03,   1.29556643e-03,
            1.29556643e-03,   1.05716645e-06,   1.05716645e-06,
            1.78675206e-07,   1.78675206e-07,   9.57301302e-03,
            9.57301302e-03,   2.73457911e-04,   2.73457911e-04,
            1.32024112e-06,   1.32024112e-06,   3.77133487e-08,
            3.77133487e-08,   1.19552465e-02,   9.75533570e-06,
            9.75533570e-06,   7.96023526e-09,   7.66546959e-03,
            7.66546959e-03,   3.70085038e-05,   3.70085038e-05,
            1.05716645e-06,   1.05716645e-06,   5.10394673e-09,
            5.10394673e-09,   8.30691786e-04,   8.30691786e-04,
            1.93626789e-08,   1.93626789e-08,   1.61796667e-03,
            1.61796667e-03,   2.73457911e-04,   2.73457911e-04,
            3.77133487e-08,   3.77133487e-08,   6.37405811e-09,
            6.37405811e-09,   2.02059585e-03,   2.02059585e-03,
            5.77193322e-05,   5.77193322e-05,   4.70982729e-08,
            4.70982729e-08,   1.34538575e-09,   1.34538575e-09,
            3.93558331e-03,   3.93558331e-03,   3.21138811e-06,
            3.21138811e-06,   5.42767351e-07,   5.42767351e-07,
            4.42891556e-10,   4.42891556e-10,   1.61796667e-03,
            1.61796667e-03,   7.81146217e-06,   7.81146217e-06,
            3.77133487e-08,   3.77133487e-08,   1.82078162e-10,
            1.82078162e-10,   1.12421908e-04,   1.12421908e-04,
            1.29556643e-03,   2.18967977e-04,   2.18967977e-04,
            3.70085038e-05,   3.70085038e-05,   1.78675206e-07,
            1.78675206e-07,   2.46415996e-11,   8.30691786e-04,
            8.30691786e-04,   6.77834392e-07,   6.77834392e-07,
            1.93626789e-08,   1.93626789e-08,   1.57997104e-11,
            1.57997104e-11,   2.73457911e-04,   2.73457911e-04,
            7.81146217e-06,   7.81146217e-06,   2.18967977e-04,
            2.18967977e-04,   1.05716645e-06,   1.05716645e-06,
            2.73457911e-04,   2.73457911e-04,   3.77133487e-08,
            3.77133487e-08,   6.37405811e-09,   6.37405811e-09,
            8.79064260e-13,   8.79064260e-13,   1.12421908e-04,
            1.12421908e-04,   9.17349095e-08,   9.17349095e-08,
            5.77193322e-05,   1.34538575e-09,   1.34538575e-09,
            3.13597326e-14,   3.70085038e-05,   3.70085038e-05,
            5.10394673e-09,   5.10394673e-09,   7.81146217e-06,
            7.81146217e-06,   1.82078162e-10,   1.82078162e-10,
            1.05716645e-06]

    assert_allclose(rad, x, 1e-7)
    assert_allclose(flux, y, 1e-7)


@pytest.mark.skipif('not HAS_PHOTUTILS')
def test_curve_of_growth():
    """Test the cog functionality."""
    from astropy.convolution import Gaussian2DKernel
    data = Gaussian2DKernel(1.5, x_size=25, y_size=25)
    plots = Imexamine()
    plots.set_data(data.array)
    x, y = plots.curve_of_growth(12, 12, genplot=False)

    rad = [1, 2, 3, 4, 5, 6, 7, 8]
    flux = [0.04535423476987057,
            0.34605795394960859,
            0.70094774639729907,
            0.89675381769455764,
            0.97242001951216395,
            0.99711765053819645,
            0.99965838382174854,
            0.99998044756724924]

    assert_array_equal(rad, x)
    assert_allclose(flux, y, 1e-6)
