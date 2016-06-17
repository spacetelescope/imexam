imexam
======

.. image:: https://travis-ci.org/spacetelescope/imexam.svg?branch=master
    :target: https://travis-ci.org/spacetelescope/imexam
    :alt: CI Testing Status

.. image:: https://readthedocs.org/projects/imexam/badge/?version=latest
    :target: https://readthedocs.org/projects/imexam/?badge=latest
    :alt: Documentation Status

.. image:: https://coveralls.io/repos/github/spacetelescope/imexam/badge.svg?branch=master 
    :target: https://coveralls.io/github/spacetelescope/imexam?branch=master
    :alt: Test Coverage Status


imexam is an affiliated package of `AstroPy`_. It was designed to be a lightweight library which enables users to explore data from a command line interface, through a Jupyter notebook or through a Jupyter console. It can be used with multiple viewers, such as DS9 or Ginga, or without a viewer as a simple library to make plots and grab quick photometry information.

For more information please see the `online documentation <http://imexam.readthedocs.io/>`_

You can also display the docs locally after install, import imexam and then issue the following command to display the help docs in your local browser:

::

    imexam.display_help()

To install using pip:

::

    pip install imexam

    pip install --upgrade imexam #if you already have an older version installed


If you receive a message like this on your Mac OSX Lion+ machine when imexam.imexam() runs:

::

    2016-02-01 11:16:11.453 python[84657:2506524] ApplePersistenceIgnoreState: Existing state will not be touched.


Try turning off the resume state:

::

    defaults write org.python.python ApplePersistenceIgnoreState NO





Launching multiple DS9 windows
------------------------------

You can launch multiple ds9 windows either from this package or the command line.
If you launch ds9 from outside the imexam package, you need supply the name of the window to imexam, this can be done in one of 2 ways:

* launch ds9 with a unique title name:

::

    ds9 -title astronomy&

then supply imexam the name of the window:

::

    a=imexam.ds9('astronomy')

* launch ds9 with nothing:

::

    ds9&

then supply imexam with the XPA_METHOD from the XPA information window, this variable will
contain either the INET address or the local filename representing the socket:

::

    a=imexam.connect('82a7e674:51763')


Starting a new connection with no target specified will open a new DS9 window using a local socket by default:

::

    a=imexam.connect()
    
Connecting to a DS9 window which was started from the system prompt:

::

    imexam.list_active_ds9() # will give you the INET address or names of the open session
    a=imexam.connect('address from the above listing')


Starting a connection to a Ginga widget, HTML5 canvas backend for browser and Jupyter viewing:

::

    a=imexam.connect(viewer='ginga')


Examples can be found in the package documentation, online documentation, and imexam.display_help() will pull up the installed package documentation in a web browser. You can also download the examply Jupyter notebooks available in the example_notebooks directory above.


You can also just load the plotting library and NOT connect to any viewer:

::

    from imexam import Imexamine
    import numpy as np

    plots = Imexamine()
    data = np.random.rand(100,100) * np.ones((100,100))
    plots.plot_line(35,45,data) #shows a matplotlib window with a plot
    plots.save() #saves the current plot to file
    
    You can also set the data attribute of the plots object and then just call many plots without specifying the data again:
    
    plots.set_data(data)
    plots.plot_line(35,45)


License
-------

imexam is licensed under a 3-clause BSD style license (see the
``licenses/LICENSE.rst`` file).

.. _AstroPy: http://www.astropy.org/
