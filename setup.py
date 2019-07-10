#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import sys
import os
from distutils.command.clean import clean
from setuptools import setup, find_packages, Command, Extension
from setuptools.command.test import test as TestCommand

if sys.version_info < (3, 5):
    error = """
    Python 3.5 and above is required.
    """
    sys.exit(error)


if not sys.platform.startswith('win'):
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


class PyTest(TestCommand):

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = [PACKAGENAME]

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        try:
            import pytest
        except ImportError:
            print('Unable to run tests...')
            print('To continue, please install "pytest":')
            print('    pip install pytest')
            exit(1)

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


try:
    from sphinx.cmd.build import build_main
    from sphinx.setup_command import BuildDoc

    class BuildSphinx(BuildDoc):
        """Build Sphinx documentation after compiling C source files"""

        description = 'Build Sphinx documentation'
        user_options = BuildDoc.user_options[:]
        user_options.append(
            ('keep-going', 'k',
             'Parses the sphinx output and sets the return code to 1 if there '
             'are any warnings. Note that this will cause the sphinx log to '
             'only update when it completes, rather than continuously as is '
             'normally the case.'))

        def initialize_options(self):
            BuildDoc.initialize_options(self)

        def finalize_options(self):
            BuildDoc.finalize_options(self)

        def run(self):
            build_cmd = self.reinitialize_command('build_ext')
            build_cmd.inplace = 1
            self.run_command('build_ext')
            retcode = build_main(['-W', '--keep-going', '-b', 'html', './docs', './docs/_build/html'])
            if retcode != 0:
                sys.exit(retcode)

except ImportError:
    class BuildSphinx(Command):
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            print('!\n! Sphinx is not installed!\n!', file=sys.stderr)
            exit(1)


try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

conf = ConfigParser()
conf.read(['setup.cfg'])

# Get some values from the setup.cfg
metadata = dict(conf.items('metadata'))
PACKAGENAME = metadata.get('package_name', 'imexam')
DESCRIPTION = metadata.get('description', 'Astropy affiliated package')
LONG_DESCRIPTION = metadata.get('long_description', 'A package to help perform \
                                image examination and plotting')
AUTHOR = metadata.get('author', 'STScI')
AUTHOR_EMAIL = metadata.get('author_email', 'help@stsci.edu')
LICENSE = metadata.get('license', 'BSD-3-Clause')
URL = metadata.get('url', 'http://astropy.org')
HOMEPAGE = metadata.get('homepage', '')


cmdclass = {'test': PyTest,
            'build_sphinx': BuildSphinx,
            }


package_data = {PACKAGENAME: []}
ext = []

if not sys.platform.startswith('win'):
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

    package_data[PACKAGENAME].extend(XPA_FILES)

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

        class my_clean(Command):
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
                                           ('build_temp', 'build_temp'))
                self.set_undefined_options('bdist',
                                           ('bdist_base', 'bdist_base'))

            def run(self):
                import subprocess
                subprocess.call(["make", "clean"],
                                cwd=XPALIB_DIR)
                if os.access(CONF_H_NAME, os.F_OK):
                    os.remove(CONF_H_NAME)
                os.remove("wrappers/xpa.c")
                clean.run(self)
                print("cleaning")

        class BuildExtWithConfigure(build_ext):
            def build_extensions(self):
                import subprocess
                subprocess.call(["make", "-f", "Makefile", "clean"],
                                cwd=XPALIB_DIR)
                subprocess.call(["sh", "./configure"], cwd=XPALIB_DIR)
                subprocess.call(["make", "-f", "Makefile"], cwd=XPALIB_DIR)
                build_ext.build_extensions(self)

        cmdclass.update({'build_ext': BuildExtWithConfigure,
                         'clean': my_clean})

    else:
        ext = [xpa_module]


setup(
    name=PACKAGENAME,
    description=DESCRIPTION,
    setup_requires=['setuptools_scm'],
    provides=[PACKAGENAME],
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    long_description=LONG_DESCRIPTION,
    use_2to3=False,
    use_scm_version=True,
    zip_safe=False,
    cmdclass=cmdclass,
    package_data=package_data,
    package_dir={'': './'},
    ext_modules=ext,
)
