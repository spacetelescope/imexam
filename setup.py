#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

# NOTE: The configuration for the package, including the name, version, and
# other information are set in the setup.cfg file.

import sys

# First provide helpful messages if contributors try and run legacy commands
# for tests or docs.

TEST_HELP = """
Note: running tests is no longer done using 'python setup.py test'. Instead
you will need to run:

    tox -e test

If you don't already have tox installed, you can install it with:

    pip install tox

If you only want to run part of the test suite, you can also use pytest
directly with::

    pip install -e .[test]
    pytest

For more information, see:

  http://docs.astropy.org/en/latest/development/testguide.html#running-tests
"""

if 'test' in sys.argv:
    print(TEST_HELP)
    sys.exit(1)

DOCS_HELP = """
Note: building the documentation is no longer done using
'python setup.py build_docs'. Instead you will need to run:

    tox -e build_docs

If you don't already have tox installed, you can install it with:

    pip install tox

You can also build the documentation with Sphinx directly using::

    pip install -e .[docs]
    cd docs
    make html

For more information, see:

  http://docs.astropy.org/en/latest/install.html#builddocs
"""

if 'build_docs' in sys.argv or 'build_sphinx' in sys.argv:
    print(DOCS_HELP)
    sys.exit(1)


import os
import importlib
from distutils.command.clean import clean
from setuptools.command.install import install
from setuptools import setup, Command, Extension
from subprocess import check_call, CalledProcessError

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

conf = ConfigParser()
conf.read(['setup.cfg'])

# Get some values from the setup.cfg
metadata = dict(conf.items('metadata'))
PACKAGENAME = metadata.get('name', 'imexam')
package_data = {PACKAGENAME: []}

ext = []
cmdclass = {}

if not sys.platform.startswith('win'):
    try:
        from Cython.Distutils import build_ext
        from Cython.Build import cythonize
        use_cython = True
        print("Cython found")
        CYTHON_SOURCE = "wrappers/xpa.pyx"
    except ImportError:
        from distutils.command import build_ext
        use_cython = False
        print("Cython not found")
        CYTHON_SOURCE = "wrappers/xpa.c"

    XPALIB_DIR = "./cextern/xpa/"
    XPA_LIBNAME = "imexamxpa"
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

    package_data[PACKAGENAME].extend(XPA_FILES)
    suffix_lib = importlib.machinery.EXTENSION_SUFFIXES[0]
    package_data[PACKAGENAME].append(XPA_LIBNAME+suffix_lib)

    XPA_SOURCES = [os.path.join(XPALIB_DIR, c) for c in XPA_FILES]
    XPALIB_DEFINES = [("HAVE_CONFIG_H", "1")]
    XPA_SOURCES.append(CYTHON_SOURCE)

    xpa_module = Extension("imexam."+XPA_LIBNAME,
                           sources=XPA_SOURCES,
                           include_dirs=[XPALIB_DIR],
                           define_macros=XPALIB_DEFINES,
                           depends=[CONF_H_NAME],
                           )
    if use_cython:
        ext = cythonize(xpa_module)
        current_env = sys.prefix

        class my_clean(Command):
            """ This is a full on clean, including docs"""
            user_options = []

            def initialize_options(self):
                self.build_base = None
                self.build_lib = None
                self.build_temp = None
                self.build_scripts = None
                self.bdist_base = None
                self.all = None

            def finalize_options(self):
                self.set_undefined_options('build',
                                           ('build_base', 'build_base'),
                                           ('build_lib', 'build_lib'),
                                           ('build_scripts', 'build_scripts'),
                                           ('build_temp', 'build_temp'),
                                           )
                self.set_undefined_options('bdist',
                                           ('bdist_base', 'bdist_base'))

            def run(self):
                try:
                    if os.access(XPALIB_DIR + "Makefile", os.F_OK):
                        check_call(["make", "clean"], cwd=XPALIB_DIR)
                except CalledProcessError as e:
                    print(e)
                    exit(1)
                if os.access(CONF_H_NAME, os.F_OK):
                    os.remove(CONF_H_NAME)
                os.remove("wrappers/xpa.c")

                xpa_bins = ["xpaaccess",
                            "xpaget",
                            "xpainfo",
                            "xpamb",
                            "xpans",
                            "xpaset",
                            ]
                for file in xpa_bins:
                    myfile = current_env + "/bin/" + file
                    if os.access(myfile, os.F_OK):
                        print(f"removing {myfile}")
                        os.remove(myfile)
                    if os.access(XPA_LIBNAME+suffix_lib, os.F_OK):
                        os.remove(XPA_LIBNAME+suffix_lib)
                try:
                    check_call(["make", "clean"], cwd="./docs")
                except CalledProcessError as e:
                    print(e)
                clean.run(self)

        class InstallWithRemake(install):
            """Configure, build, and install the aXe C code."""
            user_options = install.user_options +\
                [('noremake', None, "Don't rebuild the C executables [default True]")]

            def initialize_options(self):
                super().initialize_options()
                self.noremake = None
                self.remake = True

            def finalize_options(self):
                super().finalize_options()
                self.inplace = 1
                if self.noremake:
                    if not os.access(XPALIB_DIR + "Makefile", os.F_OK):
                        raise FileNotFoundError("Makefile doesn't exist, let imexam build")
                    else:
                        self.remake = False

            def run(self):
                if self.remake:
                    try:
                        check_call(["sh", "./configure",
                                    "--prefix="+current_env], cwd=XPALIB_DIR)
                        check_call(["make", "install"], cwd=XPALIB_DIR)
                    except CalledProcessError as e:
                        print(e)
                        exit(1)
                install.run(self)

        class BuildExtWithConfigure(build_ext):
            """Configure, build, and install the aXe C code."""

            def initialize_options(self):
                super().initialize_options()
                self.inplace = 1

            def build_extensions(self):
                super().build_extensions()

            def run(self):
                try:
                    check_call(["sh", "./configure",
                                "--prefix="+current_env], cwd=XPALIB_DIR)
                    check_call(["make", "clean"], cwd=XPALIB_DIR)
                    check_call(["make", "install"], cwd=XPALIB_DIR)
                except CalledProcessError as e:
                    print(e)
                    exit(1)
                build_ext.run(self)

        cmdclass.update({'install': InstallWithRemake,
                         'clean': my_clean,
                         'build_ext': BuildExtWithConfigure,
                         })

    else:
        ext = [xpa_module]


VERSION_TEMPLATE = """
# Note that we need to fall back to the hard-coded version if either
# setuptools_scm can't be imported or setuptools_scm can't determine the
# version, so we catch the generic 'Exception'.
try:
    from setuptools_scm import get_version
    version = get_version(root='..', relative_to=__file__)
except Exception:
    version = '{version}'
""".lstrip()


# Import these after the above checks to ensure they are printed even if
# extensions_helpers is not installed
from setuptools import setup  # noqa


setup(use_scm_version={'write_to': os.path.join('imexam', 'version.py'),
                       'write_to_template': VERSION_TEMPLATE},
      cmdclass=cmdclass,
      package_data=package_data,
      ext_modules=ext)
