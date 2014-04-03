#!/usr/bin/env python

# This sample setup.py can be used as a template for any project using d2to1.
# Simply copy this file and, if desired, delete all the comments.  Also remove
# the 'namespace_packages' and 'packages' arguments to setup.py if this project
# does not contain any packages beloning to a namespace package.

# This import statement attempts to import the setup() function from setuptools
# (this replaces the setup() one uses from distutils.core when using plain
# distutils).
#
# If the import fails (the user doesn't have the setuptools package) it then
# uses the distribute_setup bootstrap script to install setuptools, then
# retries the import.  This is common practice for packages using
# setuptools/distribute.
try:
    from setuptools import setup, Extension
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, Extension


# check if cython is available.
cython_impls = 'Cython.Distutils.build_ext'

try:
    build_ext = __import__(cython_impls, fromlist=['build_ext']).build_ext
except:
    pass

if 'build_ext' in globals(): # cython installed
    from setuptools.command.build_ext import build_ext
    from Cython.Build import cythonize
    cythonize("wrappers/xpa.pyx")
    CYTHON_SOURCE = "wrappers/xpa.c"

import os.path
XPALIB_DIR = "cextern/xpa-2.1.15"
CONF_H_NAME = os.path.join(XPALIB_DIR, "conf.h")

class build_ext_with_configure( build_ext ):
    def build_extensions(self):
        import subprocess
        if not os.path.exists(CONF_H_NAME):
            subprocess.check_call(["sh", "./configure"],
                                  cwd=XPALIB_DIR)
        build_ext.build_extensions(self)

from distutils.command.clean import clean as _clean
class clean( _clean ):
    def run(self):
        import subprocess
        subprocess.call(["make", "-f", "Makefile", "clean"],
                        cwd=XPALIB_DIR)
        if os.path.exists(CONF_H_NAME):
            os.remove(CONF_H_NAME)
        _clean.run(self)


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

xpa_sources = [CYTHON_SOURCE]  + [os.path.join(XPALIB_DIR, c) \
                                 for c in xpalib_files]
xpalib_defines  = [("HAVE_CONFIG_H", "1")]


# The standard setup() call.  Notice, however, that most of the arguments
# normally passed to setup() are absent.  They will instead be read from the
# setup.cfg file using d2to1.
#
# In order for this to work it is necessary to specify setup_requires=['d2to1']
# If the user does not have d2to1, this will boostrap it.  Also require
# stsci.distutils to use any of the common setup_hooks included in
# stsci.distutils (see the setup.cfg for more details).
#
# The next line, which defines namespace_packages and packages is only
# necessary if this projet contains a package belonging to the stsci namespace
# package, such as stsci.distutils or stsci.tools.  This is not necessary for
# projects with their own namespace, such as acstools or pyraf.
#
# d2to1=True is required to enable d2to1 and read the remaning project metadata
# from the setup.cfg file.
#
# use_2to3 and zip_safe are common options support by setuptools; these can
# also be placed in the setup.cfg, as will be demonstrated in a future update
# to this sample package.


xpa_module=Extension("imexam.xpa", 
              sources=xpa_sources,
              include_dirs=[XPALIB_DIR],
              define_macros=xpalib_defines,
              depends=[CONF_H_NAME],
            )

setup(
    setup_requires=['d2to1>=0.2.7', 'stsci.distutils>=0.3'],
    d2to1=True,
    use_2to3=True,
    zip_safe=False,
    ext_modules=[xpa_module]
)
