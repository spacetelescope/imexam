"""Licensed under a 3-clause BSD style license - see LICENSE.rst.

Make sure that the plots in imexamine are working as expected.
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
plots = Imexamine()
plots.set_data(test_data)


@pytest.mark.skipif('not HAS_MATPLOTLIB')
def test_column_plot():
    """Check the column plot function."""
    plots.plot_column(50, 50)
    f = plt.gca()
    xplot, yplot = f.lines[0].get_xydata().T
    assert_equal(yplot, test_data[50, :])
    plt.close()

@pytest.mark.skipif('not HAS_MATPLOTLIB')
def test_line_plot():
    """check the line plot function."""
    plots.plot_line(50, 50)
    f = plt.gca()
    xplot, yplot = f.lines[0].get_xydata().T
    assert_equal(yplot, test_data[:, 50])
    plt.close()


@pytest.mark.skipif('not HAS_MATPLOTLIB')
def test_xy_coords(capsys):
    """Make sure xy coords are printed with the correct location and value."""
    out_text = """50 50  3.0"""
    plots.show_xy_coords(50, 50)
    out, err = capsys.readouterr()
    assert (out.strip() == out_text)


@pytest.mark.skipif('not HAS_MATPLOTLIB')
@pytest.mark.skipif('not HAS_PHOTUTILS')
def test_aper_phot(capsys):
    """Make sure aper phot executes and returns expected text."""
    out_text = """xc=49.500000	yc=49.500000
x              y              radius         flux           mag(zpt=25.00)                 sky           fwhm
49.50          49.50          5              134.73         19.68                         1.34           27.54
"""
    plots.aper_phot(50, 50)
    out, err = capsys.readouterr()
    print(out)
    print(out_text)
    assert out == out_text


@pytest.mark.skipif('not HAS_MATPLOTLIB')
def test_line_fit():
    """Fit a Gaussian1D line to the data."""
    fit = plots.line_fit(50, 50, form='Gaussian1D', genplot=False)
    amp = 2.8152269683542137
    mean = 49.45671107821953
    stddev = 13.051081779478146

    assert_allclose(amp, fit.amplitude, 1e-6)
    assert_allclose(mean, fit.mean, 1e-6)
    assert_allclose(stddev, fit.stddev, 1e-6)


@pytest.mark.skipif('not HAS_MATPLOTLIB')
def test_column_fit():
    """Fit a Gaussian1D column to the data."""
    fit = plots.column_fit(50, 50, form='Gaussian1D', genplot=False)
    amp = 2.8285560281694115
    mean = 49.42625526973088
    stddev = 12.791137635400535

    assert_allclose(amp, fit.amplitude, 1e-6)
    assert_allclose(mean, fit.mean, 1e-6)
    assert_allclose(stddev, fit.stddev, 1e-6)


@pytest.mark.skipif('not HAS_MATPLOTLIB')
def test_gauss_center():
    """Check the gaussian center fitting."""
    # make a 2d dataset with a gaussian at the center
    from astropy.convolution import Gaussian2DKernel
    gaussian_2D_kernel = Gaussian2DKernel(10)
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


@pytest.mark.skipif('not HAS_PHOTUTILS')
@pytest.mark.skipif('not HAS_MATPLOTLIB')
def test_radial_profile():
    """Test the radial profile function."""
    from astropy.convolution import Gaussian2DKernel
    data = Gaussian2DKernel(1.5, x_size=25, y_size=25)
    plots.set_data(data.array)
    x, y = plots.radial_profile(12, 12, genplot=False)

    rad = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    flux = [4.53542348e-02,   3.00703719e-01,   3.54889792e-01,
            1.95806071e-01,   7.56662018e-02,   2.46976310e-02,
            2.54073324e-03,   1.51802470e-04,   1.08322069e-06,
            3.60555076e-10]

    assert_array_equal(rad, x)
    assert_allclose(flux, y, 1e-6)


@pytest.mark.skipif('not HAS_MATPLOTLIB')
@pytest.mark.skipif('not HAS_PHOTUTILS')
def test_curve_of_growth():
    """Test the cog function."""
    from astropy.convolution import Gaussian2DKernel
    data = Gaussian2DKernel(1.5, x_size=25, y_size=25)
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
