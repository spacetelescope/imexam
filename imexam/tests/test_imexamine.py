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
test_data[45:55, 45:55] = 3.0
xx,yy = np.meshgrid(np.arange(100), np.arange(100))


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
    radius = 10
    apertures = photutils.CircularAperture((50, 50), radius)
    aperture_area = apertures.area()
    # dq fuq does this number come from?
    assert_equal(aperture_area, np.pi*radius**2)
    rawflux_table = photutils.aperture_photometry(
        test_data,
        apertures,
        subpixels=1,
        method="center")
    total_flux = float(rawflux_table['aperture_sum'][0])
    assert_equal(total_flux, test_data.sum())


def test_line_fit():
    """Fit a Gaussian1D line to the data."""
    plots = Imexamine()
    in_amp = 3.
    in_mean = 50.
    in_stddev = 2.
    in_const = 20.
    # Set all the lines to be Gaussians
    line_gauss = in_const + in_amp * np.exp(-0.5*((xx-in_mean)/in_stddev)**2)
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
    col_gauss = in_const + in_amp * np.exp(-0.5*((yy-in_mean)/in_stddev)**2)
    plots.set_data(col_gauss)
    fit = plots.column_fit(50, 50, form='Gaussian1D', genplot=False)
    assert_allclose(in_amp, fit.amplitude_0, 1e-6)
    assert_allclose(in_mean, fit.mean_0, 1e-6)
    assert_allclose(in_stddev, fit.stddev_0, 1e-6)
    assert_allclose(in_const, fit.c0_1, 1e-6)

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
    xx, yy = np.meshgrid(np.arange(25), np.arange(25))
    x0, y0 = np.where(data.array == data.array.max())

    rad_in = np.sqrt((xx-x0)**2 + (yy-y0)**2)
    rad_in = rad_in.ravel()
    flux_in = data.array.ravel()

    order = np.argsort(rad_in)
    rad_in = rad_in[order]
    flux_in = flux_in[order]

    plots = Imexamine()
    plots.set_data(data.array)
    # check the binned results
    plots.radial_profile_pars['pixels'][0] = False
    plots.radial_profile_pars['background'][0] = False
    rad_out, flux_out = plots.radial_profile(12, 12, genplot=False)

    good = np.where(rad_in <= np.max(rad_out))
    rad_in = rad_in[good]
    flux_in = flux_in[good]

    flux_in = np.bincount(rad_in.astype(np.int), flux_in)

    assert_array_equal(np.arange(flux_in.size), rad_out)
    assert_allclose(flux_in-flux_out, flux_out*0, atol=1e-5)


@pytest.mark.skipif('not HAS_PHOTUTILS')
def test_radial_profile_background():
    """Test the radial profile function with background subtraction"""
    from astropy.convolution import Gaussian2DKernel
    data = Gaussian2DKernel(1.5, x_size=25, y_size=25)
    xx, yy = np.meshgrid(np.arange(25), np.arange(25))
    x0, y0 = np.where(data.array == data.array.max())

    rad_in = np.sqrt((xx-x0)**2 + (yy-y0)**2)
    rad_in = rad_in.ravel()
    flux_in = data.array.ravel()

    order = np.argsort(rad_in)
    rad_in = rad_in[order]
    flux_in = flux_in[order]

    plots = Imexamine()
    plots.set_data(data.array)
    # check the binned results
    plots.radial_profile_pars['pixels'][0] = False
    plots.radial_profile_pars['background'][0] = True
    rad_out, flux_out = plots.radial_profile(12, 12, genplot=False)

    good = np.where(rad_in <= np.max(rad_out))
    rad_in = rad_in[good]
    flux_in = flux_in[good]

    flux_in = np.bincount(rad_in.astype(np.int), flux_in)

    assert_array_equal(np.arange(flux_in.size), rad_out)
    assert_allclose(flux_in-flux_out, flux_out*0, atol=1e-5)


def test_radial_profile_pixels():
    """Test the radial profile function without background subtraction"""
    from astropy.convolution import Gaussian2DKernel
    data = Gaussian2DKernel(1.5, x_size=25, y_size=25)
    xx, yy = np.meshgrid(np.arange(25), np.arange(25))
    x0, y0 = np.where(data.array == data.array.max())

    rad_in = np.sqrt((xx-x0)**2 + (yy-y0)**2)

    # It's going to crop things down apparently.
    plots = Imexamine()
    datasize = int(plots.radial_profile_pars["rplot"][0])-1
    icentery = 12
    icenterx = 12
    rad_in = rad_in[icentery-datasize:icentery+datasize,
                    icenterx-datasize:icenterx+datasize]
    flux_in = data.array[icentery-datasize:icentery+datasize,
                         icenterx-datasize:icenterx+datasize]

    rad_in = rad_in.ravel()
    flux_in = flux_in.ravel()

    order = np.argsort(rad_in)
    rad_in = rad_in[order]
    flux_in = flux_in[order]

    
    plots.set_data(data.array)
    # check the unbinned results
    plots.radial_profile_pars['pixels'][0] = True
    out_radius, out_flux = plots.radial_profile(12, 12, genplot=False)
    good = np.where(rad_in <= np.max(out_radius))
    rad_in = rad_in[good]
    flux_in = flux_in[good]

    assert_allclose(rad_in, out_radius, 1e-7)
    assert_allclose(flux_in, out_flux, 1e-7)


@pytest.mark.skipif('not HAS_PHOTUTILS')
def test_curve_of_growth():
    """Test the cog functionality."""
    from astropy.convolution import Gaussian2DKernel
    data = Gaussian2DKernel(1.5, x_size=25, y_size=25)
    plots = Imexamine()
    plots.set_data(data.array)
    rad_out, flux_out = plots.curve_of_growth(12, 12, genplot=False)

    rads = [1, 2, 3, 4, 5, 6, 7, 8]
    flux = []
    # Run the aperture phot on this to build up the expected fluxes
    plots.aper_phot_pars['genplot'][0] = False
    plots.aper_phot_pars['subsky'][0] = False

    for rad in rads:
      plots.aper_phot_pars['radius'][0] = rad
      plots.aper_phot(12,12)
      flux.append(plots.total_flux)

    assert_array_equal(rads, rad_out)
    assert_allclose(flux, flux_out, 1e-6)
