

# Uncomment the following lines to display the version number of the
# package rather than the version number of Astropy in the top line when
# running the tests.

from collections import OrderedDict

from astropy.tests.helper import enable_deprecations_as_exceptions
from astropy.tests.plugins import display


display.PYTEST_HEADER_MODULES = OrderedDict([
                                    ('imexam', 'imexam'),
                                    ('numpy', 'numpy'),
                                    ('matplotlib', 'matplotlib'),
                                    ('astropy', 'astropy')])


pytest_plugins = [
    'astropy.tests.plugins.display'
]

enable_deprecations_as_exceptions()
