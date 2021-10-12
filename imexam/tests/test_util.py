"""Licensed under a 3-clause BSD style license - see LICENSE.rst.

Make sure that the functions in util are behaving as expected
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import numpy as np
from numpy.testing import assert_equal
from astropy.io import fits
from imexam import util
import ntpath

#  testing data
test_data_zeros = np.zeros((100, 100), dtype=float)


def test_invalid_simple_fits():
    """Test for an invalid simple FITS hdu with no data in
    the primary HDU."""

    simple_fits_hdu = fits.PrimaryHDU()
    valid_file, nextend, first_image = util.check_valid(simple_fits_hdu)
    assert_equal(valid_file, False)
    assert_equal(nextend, 0)
    assert_equal(first_image, None)


def test_invalid_MEF_table():
    """Test an MEF FITS hdu that only has table data."""

    # create some binary table data
    data = np.arange(0, 1, 0.01) * np.random.rand(100)
    col = np.arange(100) + 1
    d1 = fits.Column(name="data", format='d', array=data)
    c1 = fits.Column(name="item", format='d', array=col)
    cols = fits.ColDefs([c1, d1])
    tbhdu = fits.BinTableHDU.from_columns(cols, name='TAB1')

    mef_fits_hdu = fits.HDUList()
    extension = fits.PrimaryHDU()
    mef_fits_hdu.append(tbhdu)

    mef_file, nextend, first_image = util.check_valid(mef_fits_hdu)
    assert_equal(mef_file, True)
    assert_equal(nextend, 1)
    assert_equal(first_image, None)


def test_image_and_table_extensions():
    """Validate an MEF with an image in the first and
    a table in the second extension."""

    data = np.arange(0, 1, 0.01) * np.random.rand(100)
    col = np.arange(100) + 1
    d1 = fits.Column(name="data", format='d', array=data)
    c1 = fits.Column(name="item", format='d', array=col)
    cols = fits.ColDefs([c1, d1])
    tbhdu = fits.BinTableHDU.from_columns(cols, name='TAB1')

    mef_fits_hdu = fits.HDUList()
    mef_fits_hdu.append(fits.PrimaryHDU())
    extension = fits.PrimaryHDU()

    mef_fits_hdu.append(tbhdu)
    mef_fits_hdu.append(fits.ImageHDU(test_data_zeros,
                                      header=extension.header,
                                      name='SCI1'))

    mef_file, nextend, first_image = util.check_valid(mef_fits_hdu)
    assert_equal(mef_file, True)
    assert_equal(nextend, 2)
    assert_equal(first_image, 2)


def test_drizzled_image():
    """Validate a drizzle style output, with an image in the
    primary HDU and a table in the first."""

    data = np.arange(0, 1, 0.01) * np.random.rand(100)
    col = np.arange(100) + 1
    d1 = fits.Column(name="data", format='d', array=data)
    c1 = fits.Column(name="item", format='d', array=col)
    cols = fits.ColDefs([c1, d1])
    tbhdu = fits.BinTableHDU.from_columns(cols, name='TAB1')

    mef_fits_hdu = fits.HDUList()
    extension = fits.PrimaryHDU()
    mef_fits_hdu.append(fits.ImageHDU(test_data_zeros,
                                      header=extension.header))
    mef_fits_hdu.data = test_data_zeros
    mef_fits_hdu.append(tbhdu)
    mef_file, nextend, first_image = util.check_valid(mef_fits_hdu)
    assert_equal(mef_file, True)
    assert_equal(nextend, 1)
    assert_equal(first_image, 0)


def test_mef_2_image_extensions():
    """Check the file to see if it is a multi-extension FITS file
    or a simple fits image where the data and header are stored in
    the primary hdr.

    testa valid MEF file with 2 image extensions
    and the first image in the first extension
    not the primary HDU
    """

    mef_fits_hdu = fits.HDUList()
    mef_fits_hdu.append(fits.PrimaryHDU())
    extension = fits.PrimaryHDU()
    extension.header['EXTVER'] = 1
    mef_fits_hdu.append(fits.ImageHDU(test_data_zeros,
                                      header=extension.header,
                                      name='SCI1'))
    extension.header['EXTVER'] = 2
    mef_fits_hdu.append(fits.ImageHDU(test_data_zeros,
                                      header=extension.header,
                                      name='SCI2'))

    mef_file, nextend, first_image = util.check_valid(mef_fits_hdu)
    assert_equal(mef_file, True)
    assert_equal(nextend, 2)
    assert_equal(first_image, 1)


def test_simple_image_in_primary():
    """Check the file to see if it is a multi-extension FITS file
    or a simple fits image where the data and header are stored in
    the primary hdr.

    This will try and find an image data unit in the primary HDU
    """
    simple_fits_hdu = fits.PrimaryHDU()
    simple_fits_hdu.data = test_data_zeros

    mef_file, nextend, first_image = util.check_valid(simple_fits_hdu)
    assert_equal(mef_file, False)
    assert_equal(nextend, 0)
    assert_equal(first_image, 0)


def test_hst_filename():
    """Verify basename of a standard hst filename."""

    hst_name = "hstimagex_cal.fits"
    shortname, extname, extver = util.verify_filename(filename=hst_name)
    short_compare = ntpath.basename(shortname)
    assert_equal(hst_name, short_compare)
    assert_equal(extname, None)
    assert_equal(extver, None)


def test_ext_ver_filename():
    """Verify basename of a filname given with ext and ver."""

    hst_name_ext_ver = "hstimagex_cal.fits[sci,1]"
    rootname = "hstimagex_cal.fits"
    shortname, extname, extver = util.verify_filename(filename=hst_name_ext_ver)
    short_compare = ntpath.basename(shortname)
    assert_equal(rootname, short_compare)
    assert_equal(extname, "sci")
    assert_equal(extver, 1)


def test_name_ver_filename():
    """Verify basename of a filename given name and ver."""

    hst_name_ver = "hstimagex_cal.fits[1]"
    rootname = "hstimagex_cal.fits"
    shortname, extname, extver = util.verify_filename(filename=hst_name_ver)
    short_compare = ntpath.basename(shortname)
    assert_equal(rootname, short_compare)
    assert_equal(extname, None)
    assert_equal(extver, 1)


def test_extver():
    """Verify that specifying an extver gets recorded correctly.

    extver is the extension number explicitly"""

    hst_name = "hstimagex_cal.fits"
    shortname, extname, extver = util.verify_filename(filename=hst_name,
                                                      extver=1)
    short_compare = ntpath.basename(shortname)
    assert_equal(hst_name, short_compare)
    assert_equal(extname, None)
    assert_equal(extver, 1)


def test_extname():
    """Verify that specifying an extname gets recorded correctly."""

    hst_name = "hstimagex_cal.fits"
    shortname, extname, extver = util.verify_filename(filename=hst_name,
                                                      extname='sci')
    short_compare = ntpath.basename(shortname)
    assert_equal(hst_name, short_compare)
    assert_equal(extname, 'sci')
    assert_equal(extver, None)


def test_name_ver():
    """Verify that specifying both name and ver gets recorded correctly."""

    hst_name = "hstimagex_cal.fits"
    shortname, extname, extver = util.verify_filename(filename=hst_name,
                                                      extname='sci',
                                                      extver=1)
    short_compare = ntpath.basename(shortname)
    assert_equal(hst_name, short_compare)
    assert_equal(extname, 'sci')
    assert_equal(extver, 1)
