#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

from glob import glob
import sys
import os


from setuptools import setup
from distutils.extension import Extension
from distutils.command.clean import clean

import ah_bootstrap
from astropy_helpers.setup_helpers import (
    register_commands, adjust_compiler, get_debug_option, get_package_info)
from astropy_helpers.git_helpers import get_git_devstr
from astropy_helpers.version_helpers import generate_version_py

try:
    from Cython.Distutils import build_ext
    from Cython.Build import cythonize
    use_cython = True
    CYTHON_SOURCE = "wrappers/xpa.pyx"
except ImportError:
    from distutils.command import build_ext
    use_cython = False
    print("Building without Cython")
    CYTHON_SOURCE = "wrappers/xpa.c"

# A dirty hack to get around some early import/configurations ambiguities
if sys.version_info[0] >= 3:
    import builtins
else:
    import __builtin__ as builtins

# Get some values from the setup.cfg
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

conf = ConfigParser()

conf.read(['setup.cfg'])

# Get some values from the setup.cfg
metadata = dict(conf.items('metadata'))

PACKAGENAME = metadata.get('package_name', 'packagename')
DESCRIPTION = metadata.get('description', 'Astropy affiliated package')
LONG_DESCRIPTION = metadata.get('long_description', 'A package to help perform \
                                image examination and plotting')
AUTHOR = metadata.get('author', '')
AUTHOR_EMAIL = metadata.get('author_email', '')
LICENSE = metadata.get('license', 'unknown')
URL = metadata.get('url', 'http://astropy.org')

builtins._ASTROPY_SETUP_ = True

# VERSION should be PEP386 compatible (http://www.python.org/dev/peps/pep-0386)
VERSION = '0.6.dev'

# Indicates if this version is a release version
RELEASE = 'dev' not in VERSION
if not RELEASE:
    VERSION += get_git_devstr(False)


# Populate the dict of setup command overrides; this should be done before
# invoking any other functionality from distutils since it can potentially
# modify distutils' behavior.
cmdclass = register_commands(PACKAGENAME, VERSION, RELEASE)

# Freeze build information in version.py
generate_version_py(PACKAGENAME, VERSION, RELEASE,
                    get_debug_option(PACKAGENAME))

# Get configuration information from all of the various subpackages.
# See the docstring for setup_helpers.update_package_files for more
# details.
package_info = get_package_info()

# Store the package name in a built-in variable so it's easy
# to get from other parts of the setup infrastructure
builtins._ASTROPY_PACKAGE_NAME_ = PACKAGENAME

# Add the project-global data
package_info['package_data'].setdefault(PACKAGENAME, [])

XPALIB_DIR = "cextern/xpa/"
CONF_H_NAME = os.path.join(XPALIB_DIR, "conf.h")

# We only need to compile with these
XPA_FILES = """acl.c
               client.c
               clipboard.c
               command.c
               find.c
               port.c
               remote.c
               tcp.c
               timedconn.c
               word.c
               xalloc.c
               xlaunch.c
               xpa.c
               xpaio.c
               """.split()

XPA_SOURCES = [os.path.join(XPALIB_DIR, c) for c in XPA_FILES]
XPALIB_DEFINES = [("HAVE_CONFIG_H", "1")]
XPA_SOURCES.append(CYTHON_SOURCE)

xpa_module = Extension("xpa",
                       sources=XPA_SOURCES,
                       include_dirs=[XPALIB_DIR],
                       define_macros=XPALIB_DEFINES,
                       depends=[CONF_H_NAME],
                       )
if use_cython:
    ext = cythonize(xpa_module)

    class my_clean(clean):
        def run(self):
            import subprocess
            subprocess.call(["make", "clean"],
                            cwd=XPALIB_DIR)
            if os.access(CONF_H_NAME, os.F_OK):
                os.remove(CONF_H_NAME)
            clean.run(self)
            print("cleaning")

    class build_ext_with_configure(build_ext):
        def build_extensions(self):
            import subprocess
            subprocess.call(["make", "-f", "Makefile", "clean"],
                            cwd=XPALIB_DIR)
            subprocess.call(["sh", "./configure"], cwd=XPALIB_DIR)
            subprocess.call(["make", "-f", "Makefile"], cwd=XPALIB_DIR)
            build_ext.build_extensions(self)

    cmdclass.update({'build_ext': build_ext_with_configure, 'clean': my_clean})

else:
    ext = [xpa_module]


package_info['ext_modules'] = ext
package_info['packages'] = ['imexam', 'xpa']

setup(
    name=PACKAGENAME,
    version=VERSION,
    description=DESCRIPTION,
    requires=['astropy'],
    install_requires=['astropy'],
    provides=[PACKAGENAME],
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    long_description=LONG_DESCRIPTION,
    d2to1=True,
    use_2to3=False,
    zip_safe=False,
    cmdclass=cmdclass,
    **package_info
)
