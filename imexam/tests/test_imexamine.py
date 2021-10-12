"""Licensed under a 3-clause BSD style license - see LICENSE.rst.

Make sure that the basic plots in imexamine are working as expected.
"""
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
    from packaging import version
    photutils_version = version.parse(photutils.__version__)
except ImportError:
    HAS_PHOTUTILS = False


# make some data to test with
test_data = np.zeros((100, 100), dtype=float)
test_data[45:55, 45:55] = 3.0
xx, yy = np.meshgrid(np.arange(100), np.arange(100))


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
    radius = 5
    apertures = photutils.CircularAperture((50, 50), radius)
    if photutils_version >= version.parse('0.7'):
        aperture_area = apertures.area
    else:
        aperture_area = apertures.area()
    assert_equal(aperture_area, np.pi * radius**2)
    rawflux_table = photutils.aperture_photometry(
        test_data,
        apertures,
        subpixels=1,
        method="center")
    total_flux = float(rawflux_table['aperture_sum'][0])
    # Verify the expected circular area sum
    assert_equal(total_flux, 207.0)


def test_line_fit():
    """Fit a Gaussian1D line to the data."""
    plots = Imexamine()
    in_amp = 3.
    in_mean = 50.
    in_stddev = 2.
    in_const = 20.

    # Set all the lines to be Gaussians
    line_gauss = in_const + in_amp * np.exp(-0.5 * ((xx - in_mean) / in_stddev)**2)
    plots.set_data(line_gauss)
    fit = plots.line_fit(50, 50, form='Gaussian1D', genplot=False)

    assert_allclose(in_amp, fit.amplitude_0, 1e-6)
    assert_allclose(in_mean, fit.mean_0, 1e-6)
    assert_allclose(in_stddev, fit.stddev_0, 1e-6)
    assert_allclose(in_const, fit.c0_1, 1e-6)


def test_column_fit():
    """Fit a Gaussian1D column to the data."""
    plots = Imexamine()
    in_amp = 3.
    in_mean = 50.
    in_stddev = 2.
    in_const = 20.
    # Set all the columns to be Gaussians
    col_gauss = in_const + in_amp * np.exp(-0.5 * ((yy - in_mean) / in_stddev)**2)
    plots.set_data(col_gauss)
    fit = plots.column_fit(50, 50, form='Gaussian1D', genplot=False)

    assert_allclose(in_amp, fit.amplitude_0, 1e-6)
    assert_allclose(in_mean, fit.mean_0, 1e-6)
    assert_allclose(in_stddev, fit.stddev_0, 1e-6)
    assert_allclose(in_const, fit.c0_1, 1e-6)


def test_gauss_center():
    """Check the gaussian center fitting."""

    from astropy.convolution import Gaussian2DKernel

    # This creates a 2D normalized gaussian kernal with
    # a set amplitude. Guess off-center
    amp = 0.0015915494309189533
    size = 81.0
    sigma = 10.0

    gaussian_2D_kernel = Gaussian2DKernel(sigma, x_size=size, y_size=size)
    plots = Imexamine()
    plots.set_data(gaussian_2D_kernel.array)
    a, xx, yy, xs, ys = plots.gauss_center(37, 37)

    assert_allclose(amp, a, 1e-6)
    assert_allclose(size // 2, xx, 1e-6)
    assert_allclose(size // 2, yy, 1e-6)
    assert_allclose(sigma, xs, 0.01)
    assert_allclose(sigma, ys, 0.01)


def test_radial_profile():
    """Test the radial profile function
    No background subtraction
    individual pixel results used
    """
    from astropy.convolution import Gaussian2DKernel
    data = Gaussian2DKernel(1.5, x_size=25, y_size=25)
    xx, yy = np.meshgrid(np.arange(25), np.arange(25))
    x0, y0 = np.where(data.array == data.array.max())

    rad_in = np.sqrt((xx - x0)**2 + (yy - y0)**2)
    rad_in = rad_in.ravel()
    flux_in = data.array.ravel()

    order = np.argsort(rad_in)
    rad_in = rad_in[order]
    flux_in = flux_in[order]

    plots = Imexamine()
    plots.set_data(data.array)

    plots.radial_profile_pars['pixels'][0] = True
    plots.radial_profile_pars['background'][0] = False
    plots.radial_profile_pars['clip'][0] = False
    rad_out, flux_out = plots.radial_profile(x0, y0, genplot=False)

    order2 = np.argsort(rad_out)
    rad_out = rad_out[order2]
    flux_out = flux_out[order2]

    # the radial profile is done on a smaller cutout by default
    # and may have a fractional center radius calculation. This
    # looks at the first few hundred data points in both arrays
    assert (len(rad_out) < len(rad_in))
    good = 150
    assert_allclose(rad_in[:good], rad_out[:good], atol=1e-14)
    assert_allclose(flux_in[:good], flux_out[:good], atol=1e-14)


def test_radial_profile_cumulative():
    """Test the radial profile function
    without background subtraction
    with each pixel integer binned
    """
    from astropy.convolution import Gaussian2DKernel
    ksize = 25
    data = Gaussian2DKernel(1.5, x_size=ksize, y_size=ksize)
    xx, yy = np.meshgrid(np.arange(ksize), np.arange(ksize))
    x0, y0 = np.where(data.array == data.array.max())
    rad_in = np.sqrt((xx - x0)**2 + (yy - y0)**2)

    rad_in = rad_in.ravel()
    flux_in = data.array.ravel()

    indices = np.argsort(rad_in)
    rad_in = rad_in[indices]
    flux_in = flux_in[indices]

    # now bin the radflux like we expect
    rad_in = rad_in.astype(int)
    flux_in = np.bincount(rad_in, flux_in) / np.bincount(rad_in)
    rad_in = np.arange(len(flux_in))
    assert (data.array[x0, y0] == flux_in[0])

    # check the binned results
    plots = Imexamine()
    plots.set_data(data.array)
    plots.radial_profile_pars['pixels'][0] = False
    plots.radial_profile_pars['background'][0] = False
    plots.radial_profile_pars['clip'][0] = False
    rad_out, flux_out = plots.radial_profile(x0, y0, genplot=False)

    # The default measurement size is not equal
    assert (len(rad_in) >= len(rad_out))
    good = [rad_in[i] for i in rad_out if rad_out[i] == rad_in[i]]

    assert_array_equal(rad_in[good], rad_out[good])
    assert_allclose(flux_in[good], flux_out[good], atol=1e-7)


@pytest.mark.skipif('not HAS_PHOTUTILS')
def test_curve_of_growth():
    """Test the curve of growth functionality."""
    from astropy.modeling.models import Gaussian2D
    y, x = np.mgrid[0:101, 0:101]
    xcen = ycen = 50
    model = Gaussian2D(1.5, xcen, ycen, 3, 3)
    data = model(x, y)
    plots = Imexamine()
    plots.set_data(data)
    rad_out, flux_out = plots.curve_of_growth(xcen, ycen, genplot=False)

    rads = [1, 2, 3, 4, 5, 6, 7, 8]
    flux = []

    # Run the aperture phot on this to build up the expected fluxes
    plots.aper_phot_pars['subsky'][0] = False
    plots.aper_phot_pars['center_com'][0] = False

    for rad in rads:
        plots.aper_phot_pars['radius'][0] = rad
        apertures, annulus_apertures, rawflux_table, sky_per_pix = plots.aper_phot(xcen, ycen, genplot=False)
        flux.append(rawflux_table['aperture_sum'][0])

    assert_array_equal(rads, rad_out)
    assert_allclose(flux, flux_out, 1e-6)
