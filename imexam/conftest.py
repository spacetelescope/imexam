

# Uncomment the following lines to display the version number of the
# package rather than the version number of Astropy in the top line when
# running the tests.

import os
import pytest
from collections import OrderedDict

from . import __version__

from astropy.tests.helper import enable_deprecations_as_exceptions
from astropy.tests.plugins import display


display.PYTEST_HEADER_MODULES = OrderedDict([
                                    ('imexam', 'imexam'),
                                    ('numpy', 'numpy'),
                                    ('matplotlib', 'matplotlib'),
                                    ('astropy', 'astropy')])


enable_deprecations_as_exceptions()
