#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import sys
import os
import importlib
from distutils.command.clean import clean
from setuptools.command.install import install
from setuptools.command.build_py import build_py
from setuptools import setup, Command, Extension
from setuptools.command.test import test as TestCommand
from subprocess import check_call, CalledProcessError


if sys.version_info < (3, 5):
    error = """ERROR: imexam requires python >= 3.5."""
    sys.exit(error)


class PyTest(TestCommand):
    user_options = []

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ["--cov", PACKAGENAME]

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
            try:
                import imexam
            except ImportError as e:
                build_cmd = self.reinitialize_command('build_ext')
                build_cmd.inplace = 1
            retcode = build_main(['-W', '--keep-going', '-b', 'html', './docs', './docs/_build/html'])
            if retcode != 0:
                sys.exit(retcode)

except ImportError:
    print("Sphinx is not installed, can't build documents!!\n")
    class BuildSphinx(Command):
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            pass


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




package_data = {PACKAGENAME: []}
ext = []

cmdclass = {'test': PyTest,
            'build_sphinx': BuildSphinx,
            }


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
    suffix_lib =  importlib.machinery.EXTENSION_SUFFIXES[0]
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
                        check_call(["sh", "./configure","--prefix="+current_env], cwd=XPALIB_DIR)
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
                    check_call(["sh", "./configure","--prefix="+current_env], cwd=XPALIB_DIR)
                    check_call(["make", "clean"],cwd=XPALIB_DIR)
                    check_call(["make", "install"], cwd=XPALIB_DIR)
                except CalledProcessError as e:
                    print(e)
                    exit(1)
                build_ext.run(self)

                

        cmdclass.update({'install' : InstallWithRemake,
                         'clean' : my_clean,
                         'build_ext' : BuildExtWithConfigure,
                         })

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
    package_dir={'imexam': 'imexam'},
    ext_modules=ext,
)