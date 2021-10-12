======
imexam
======

|CI Status| |Latest RTD Status| |Coveralls| |Astropy| |Zenodo|

imexam is an affiliated package of `AstroPy`_. It was designed to be a
lightweight library which enables users to explore data from a command
line interface, through a Jupyter notebook or through a Jupyter console.
It can be used with multiple viewers, such as DS9 or Ginga, or without
a viewer as a simple library to make plots and grab quick photometry
information. It has been designed so that other viewers may be easily
attached in the future.

For more information please see the `online documentation
<http://imexam.readthedocs.io/>`_


Note: There is one git submodule in this package, a submodule for the
xpa code that talks to DS9. If you are planning to work on developing
new code or installing this package from a repo download, you need to
pull the xpa code using the following command after you have cloned the
repository and before you "python setup.py install"

::

    git submodule update --init -- cextern/xpa


If you are cloning the repository for the first time, you can do both steps at once using a recursive clone:

::

    git clone --recursive https://github.com/spacetelescope/imexam.git

You can also display the docs locally after install, import imexam and then issue the following command to display the help docs in your local browser:

::

    imexam.display_help()

To install using pip:

::

    pip install imexam   #installs from the most recent pypi binaries

    pip install git+https://github.com/spacetelescope/imexam  #installs from the current master on this repo

    pip install --upgrade imexam #if you already have an older version installed


If you receive a message like this on your Mac OSX Lion+ machine when
imexam.imexam() runs:

::

    2016-02-01 11:16:11.453 python[84657:2506524] ApplePersistenceIgnoreState: Existing state will not be touched.


Try turning off the resume state:

::

    defaults write org.python.python ApplePersistenceIgnoreState NO


Contributing
============
Please open a new issue or new pull request for bugs, feedback, or new
features you would like to see. If there is an issue you would like to
work on, please leave a comment and we will be happy to assist. New
contributions and contributors are very welcome!

New to GitHub or open source projects? If you are unsure about where
to start or haven't used github before, please feel free to contact
`@sosey`. Want more information about how to make a contribution? Take a
look at the astropy `contributing`_ and `developer`_ documentation.

Feedback and feature requests? Is there something missing you would
like to see? Please open an issue or send an email to `@sosey`. imexam
follows the `Astropy Code of Conduct`_ and strives to provide a
welcoming community to all of our users and contributors.


License
=======
imexam is licensed under a 3-clause BSD style license (see the
``licenses/LICENSE.rst`` file).

.. _AstroPy: http://www.astropy.org/
.. _contributing: http://docs.astropy.org/en/stable/index.html#contributing
.. _developer: http://docs.astropy.org/en/stable/index.html#developer-documentation
.. _Astropy Code of Conduct:  http://www.astropy.org/about.html#codeofconduct


Quick Instructions
==================
If you are having display issues, and you are using TkAgg, try setting
your matplotlib backend to Qt4Agg or Qt5Agg. You can set this in
your .matplotlib/matplotlibrc file. You may also want to switch your
matplotlib backend to Qt if you have a mac with the default MacOS
backend specified. If you don't already have matplotlibrc file in
your home directory, you can download one from their documentation:
https://matplotlib.org/_static/matplotlibrc

::

    inside ~/.matplotlib/matplotlibrc:
    backend: Qt4Agg


Using the Ginga HTML5 Viewer
----------------------------

If you have installed Ginga, you can use the HTML5 viewer for image
display with either a jupyter console, qtconsole or Jupyter notebook
session. If you are using a Windows machine you should install ginga to
use as the viewer with this package. Make sure that you have installed
the latest version, or you can download the development code here:
https://github.com/ejeschke/ginga.

There is also a ginga plugin for imexam which is in the ginga repository
in the experimental directory. This will load the imexam plotting and
analysis library into the ginga gui framework.

Starting a connection to a Ginga HTML5 canvas backend for browser and
Jupyter viewing:

::

    a = imexam.connect(viewer='ginga')

You can optionally provide a port number to which the viewer is
connected as well:

::

    a=imexam.connect(viewer='ginga', port=9856)


Using imexam with DS9
---------------------
From a python terminal: using either the TkAGG or QT4Agg/QT5Agg
backends:

::

    import imexam
    a = imexam.connect()
    a.imexam()

From an ipython terminal: using either the TkAgg or QT4Agg/QT5Agg backends.

::

    import imexam
    a = imexam.connect()

If you are using TkAGG as the backend, from an ipython terminal, you may
need to ctrl-D, then select n, to closeout the plotting window. This
should not happen if you are running TkAgg and running from a regular
python terminal. Looking into the closeout issue with TkAgg now.

From jupyter console/qtconsole: startup with the matplotlib magics to
use the backend you specified for display:

::

    In [1]: %matplotlib
    import imexam
    a = imexam.connect()

If you are using the Qt4Agg/Qt5Agg backend with ginga, the plots will
display in the console window


Launching multiple DS9 windows
------------------------------
You can launch multiple ds9 windows either from this package or the
command line. DS9 can be used to view images and arrays from any of the
python terminals, consoles or the Jupyter notebook.

If you launch ds9 from outside the imexam package, you need supply the
name of the window to imexam, this can be done in one of 2 ways:

* launch ds9 with a unique title name:

::

    ds9 -title astronomy&

then supply imexam the name of the window:

::

    a=imexam.ds9('astronomy')

* launch ds9 with nothing:

::

    ds9&

then supply imexam with the XPA_METHOD from the XPA information window,
this variable will contain either the INET address or the local filename
representing the socket:

::

    a=imexam.connect('82a7e674:51763')


Starting a new connection with no target specified will open a new DS9
window using a local socket by default:

::

    a=imexam.connect()

Connecting to a DS9 window which was started from the system prompt:

::

    imexam.list_active_ds9() # will give you the INET address or names of the open session
    a=imexam.connect('address from the above listing')


Examples can be found in the package documentation, online
documentation, and imexam.display_help() will pull up the installed
package documentation in a web browser. You can also download the
examply Jupyter notebooks available in the example_notebooks directory
above.


You can also just load the plotting library for use without a viewer:
---------------------------------------------------------------------
This is useful when you want to make batch plots or return information .
from scripts You can also save the lotting data returned and use it    .
futher, or design your own plot                                        .

::

    from imexam.imexamine import Imexamine
    import numpy as np

    plots = Imexamine()  #the plots object now has all available functions
    data = np.random.rand(100,100) * np.ones((100,100)) #make some fake data
    plots.plot_line(35,45,data) #shows a matplotlib window with a plot
    plots.save() #saves the current plot to file

    You can also set the data attribute of the plots object and then just call many plots without specifying the data again:

    plots.set_data(data)
    plots.plot_line(35,45)


.. |CI Status| image:: https://github.com/spacetelescope/imexam/workflows/CI%20Tests/badge.svg#
    :target: https://github.com/spacetelescope/imexam/actions
    :alt: CI Status

.. |Latest RTD Status| image:: https://readthedocs.org/projects/imexam/badge/?version=latest
    :target: https://readthedocs.org/projects/imexam/?badge=latest
    :alt: Documentation Status

.. |Coveralls| image:: https://coveralls.io/repos/github/spacetelescope/imexam/badge.svg?branch=master
    :target: https://coveralls.io/github/spacetelescope/imexam?branch=master
    :alt: Test Coverage Status

.. |Astropy| image:: https://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat
    :target: https://www.astropy.org/
    :alt: Powered by Astropy

.. |Zenodo| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.2283789.svg
   :target: https://doi.org/10.5281/zenodo.2283789
