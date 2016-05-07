"""Licensed under a 3-clause BSD style license - see LICENSE.rst.

The tests in this file check that the imexamine keys are working as expected
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import pytest
import numpy as np
from numpy.testing import assert_allclose, assert_equal
from imexam.imexamine import Imexamine

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


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


@pytest.mark.skipif('not HAS_MATPLOTLIB')
def test_line_plot():
    """check the line plot function."""
    plots.plot_line(50, 50)
    f = plt.gca()
    xplot, yplot = f.lines[0].get_xydata().T
    assert_equal(yplot, test_data[:, 50])


def test_xy_coords(capsys):
    """Make sure xy coords are printed with the correct location and value."""
    out_text = """50 50  3.0"""
    plots.show_xy_coords(50, 50)
    out, err = capsys.readouterr()
    assert (out.strip() == out_text)


def test_aper_phot(capsys):
    """Make sure aper phot executes and returns expected text."""
    out_text = """xc=50.500000	yc=50.500000
x              y              radius         flux           mag(zpt=25.00)                 sky           fwhm
49.50          49.50          5              134.73         19.68                         1.34           27.54
"""
    plots.aper_phot(50, 50)
    out, err = capsys.readouterr()
    print(out)
    print(out_text)
    assert out == out_text


def test_line_fit():
    """Fit a Gaussian1D line to the data."""
    fit = plots.line_fit(50, 50, form='Gaussian1D', genplot=False)
    amp = 2.8152269683542137
    mean = 49.45671107821953
    stddev = 13.051081779478146

    assert_allclose(amp, fit.amplitude, 1e-6)
    assert_allclose(mean, fit.mean, 1e-6)
    assert_allclose(stddev, fit.stddev, 1e-6)


def test_column_fit():
    """Fit a Gaussian1D column to the data."""
    fit = plots.column_fit(50, 50, form='Gaussian1D', genplot=False)
    amp = 2.8285560281694115
    mean = 49.42625526973088
    stddev = 12.791137635400535

    assert_allclose(amp, fit.amplitude, 1e-6)
    assert_allclose(mean, fit.mean, 1e-6)
    assert_allclose(stddev, fit.stddev, 1e-6)
