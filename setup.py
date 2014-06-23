#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import glob
import sys
import os

try:
    from setuptools import setup, Extension
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, Extension


# Get some values from the setup.cfg
from distutils import config
conf = config.ConfigParser()
conf.read(['setup.cfg'])
metadata = dict(conf.items('metadata'))

PACKAGENAME = metadata.get('package_name', 'packagename')
DESCRIPTION = metadata.get('description', 'Astropy affiliated package')
LONG_DESCRIPTION=metadata.get('long_description','A package to help perform image examination through a viewing tool')
AUTHOR = metadata.get('author', '')
AUTHOR_EMAIL = metadata.get('author_email', '')
LICENSE = metadata.get('license', 'unknown')
VERSION = metadata.get('version','')

# Indicates if this version is a release version
RELEASE = 'dev' not in VERSION


# Treat everything in scripts except README.rst as a script to be installed
scripts = [fname for fname in glob.glob(os.path.join('scripts', '*'))
           if os.path.basename(fname) != 'README.rst']


# check if cython is available.
try:
    from Cython.Build import cythonize
    cythonize("wrappers/xpa.pyx")
    CYTHON_SOURCE = "wrappers/xpa.c"
except ImportError:
    print("Unable to load Cython")
    raise ImportError


XPALIB_DIR = "cextern/xpa-2.1.15"
CONF_H_NAME = os.path.join(XPALIB_DIR, "conf.h")


from distutils.command.clean import clean
class my_clean(clean):

    def run(self):
        import subprocess
        subprocess.call(["make", "clean"],
                        cwd=XPALIB_DIR)
        if os.path.exists(CONF_H_NAME):
            os.remove(CONF_H_NAME)
        os.remove(CYTHON_SOURCE)
        clean.run(self)
        print("cleaning")


# uncomment this section if you want to build the full XPA
# build xpans so that we can start up the name server
# if users dont have it installed on their machine

#from setuptools.command.build_ext import build_ext
# class build_ext_with_configure(build_ext):
#
#    def build_extensions(self):
#        import subprocess
#        subprocess.call(["make","-f","Makefile","clean"],
#                cwd=XPALIB_DIR)
#        subprocess.call(["sh", "./configure"],cwd=XPALIB_DIR)
#        subprocess.call(["make", "-f", "Makefile"],cwd=XPALIB_DIR)
#        build_ext.build_extensions(self)
#        print("building with configure")


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
                  xpaio.c
                  """.split()

xpa_sources = [CYTHON_SOURCE] + [os.path.join(XPALIB_DIR, c)
                                 for c in xpalib_files]
xpalib_defines = [("HAVE_CONFIG_H", "1")]

xpa_module = Extension("imexam.xpa",
                       sources=xpa_sources,
                       include_dirs=[XPALIB_DIR],
                       define_macros=xpalib_defines,
                       depends=[CONF_H_NAME],
                       )

setup(
    name=PACKAGENAME,
    version=VERSION,
    description=DESCRIPTION,
    scripts=scripts,
    requires=['astropy'],
    install_requires=['astropy'],
    provides=[PACKAGENAME],
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    long_description=LONG_DESCRIPTION,
    setup_requires=['d2to1>=0.2.7', 'stsci.distutils>=0.3'],
    d2to1=True,
    use_2to3=True,
    zip_safe=False,
    ext_modules=[xpa_module],
)

# add this back into the setup command if you want to build the full XPA
# cmdclass={'build_ext':build_ext_with_configure,'clean':my_clean},
