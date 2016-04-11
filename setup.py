#!/usr/bin/env python
"""Licensed under a 3-clause BSD style license - see LICENSE.rst."""

import sys
import os
import ah_bootstrap

from astropy_helpers.setup_helpers import (register_commands, get_debug_option)
from astropy_helpers.git_helpers import get_git_devstr
from astropy_helpers.version_helpers import generate_version_py
from distutils import config
from distutils.core import setup
from distutils.extension import Extension
from distutils.command.clean import clean

if sys.version_info[0] >= 3:
    import builtins
else:
    import __builtin__ as builtins
builtins._ASTROPY_SETUP_ = True

try:
    from Cython.Distutils import build_ext
    from Cython.Build import cythonize
except ImportError:
    use_cython = False
else:
    use_cython = True

# Get some values from the setup.cfg
conf = config.ConfigParser()
conf.read(['setup.cfg'])
metadata = dict(conf.items('metadata'))

PACKAGENAME = metadata.get('package_name', 'packagename')
DESCRIPTION = metadata.get('description', 'Astropy affiliated package')
LONG_DESCRIPTION = metadata.get('long_description','A package to help perform command-line image examination through a viewing')
AUTHOR = metadata.get('author', '')
AUTHOR_EMAIL = metadata.get('author_email', '')
LICENSE = metadata.get('license', 'unknown')
URL = metadata.get('url', 'http://astropy.org')
VERSION = metadata.get('version', '')
CLASSIFIERS = metadata.get('classifier', '')
CYTHON_SOURCE = "wrappers/xpa.c"  # cython file
XPALIB_DIR = "cextern/xpa-2.1.15"
CONF_H_NAME = os.path.join(XPALIB_DIR, "conf.h")

# Indicates if this version is a release version
RELEASE = 'dev' not in VERSION

if not RELEASE:
    VERSION += get_git_devstr(False)

# Store the package name in a built-in variable so it's easy
# to get from other parts of the setup infrastructure
builtins._ASTROPY_PACKAGE_NAME_ = PACKAGENAME

# Populate the dict of setup command overrides; this should be done before
# invoking any other functionality from distutils since it can potentially
# modify distutils' behavior.
cmdclass = register_commands(PACKAGENAME, VERSION, RELEASE)


# Freeze build information in version.py
generate_version_py(PACKAGENAME, VERSION, RELEASE,
                    get_debug_option(PACKAGENAME))

class my_clean(clean):
    """clean all the sources on build."""

    def run(self):
        """Clean."""
        import subprocess
        subprocess.call(["make", "clean"],
                        cwd=XPALIB_DIR)
        if os.path.exists(CONF_H_NAME):
            os.remove(CONF_H_NAME)
        os.remove(CYTHON_SOURCE)
        clean.run(self)
        print("cleaning")


class build_ext_with_configure(build_ext):
    """Special build."""

    def build_extensions(self):
        """build source with configure."""
        import subprocess
        subprocess.call(["make", "-f", "Makefile", "clean"],
                        cwd=XPALIB_DIR)
        subprocess.call(["sh", "./configure"], cwd=XPALIB_DIR)
        subprocess.call(["make", "-f", "Makefile"], cwd=XPALIB_DIR)
        build_ext.build_extensions(self)
        print("building with configure")


xpalib_files = """acl.c
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
                  xpans.c
                  xpaio.c
                  """.split()

xpa_sources = [os.path.join(XPALIB_DIR, c) for c in xpalib_files]
xpa_sources.append("wrappers/xpa.pyx")
xpalib_defines = [("HAVE_CONFIG_H", "1")]

ext_modules = []  # xpa_module to build
if use_cython:
    ext_modules += [
        Extension("imexam.xpa",
                  sources=xpa_sources,
                  include_dirs=[XPALIB_DIR],
                  define_macros=xpalib_defines,
                  depends=[CONF_H_NAME],
                  )
    ]
    cmdclass.update({'build_ext': build_ext_with_configure, 'clean': my_clean})

else:
    ext_modules += [
        Extension("imexam.xpa", ["wrappers/xpa.c"]),
    ]


setup(
    name=PACKAGENAME,
    version=VERSION,
    description=DESCRIPTION,
    install_requires=['astropy'],
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    url=URL,
    long_description=LONG_DESCRIPTION,
    setup_requires=['d2to1>=0.2.7'],
    d2to1=True,
    use_2to3=False,
    zip_safe=False,
    classifiers=CLASSIFIERS,
    cmdclass=cmdclass,
    ext_modules=cythonize(ext_modules)
    )
