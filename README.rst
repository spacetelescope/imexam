imexam
======

.. image:: https://travis-ci.org/spacetelescope/imexam.svg?branch=master
    :target: https://travis-ci.org/spacetelescope/imexam

.. image:: https://readthedocs.org/projects/imexam/badge/?version=latest
    :target: https://readthedocs.org/projects/imexam/?badge=latest
    :alt: Documentation Status
                
                
imexam is an `AstroPy`_ affiliated package  meant for quick image analysis, much like the IRAF imexamine task. 
Image display is currently supported with either DS9 or a Ginga widget from a python session.

For more information please see the `online documentation <http://imexam.readthedocs.org/en/latest/imexam/index.html>`_

You can also display the docs locally after install, import imexam and then issue the following command to display the help docs in your local browser: 

::

    imexam.display_help()

To install using pip:

::

    pip install imexam
    
    pip install --upgrade imexam #if you already have an older version installed
    
    
If you recieve a message like this on your Mac OSX Lion + machine when imexam.imexam() runs:

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


Starting a connection to a Ginga widget, HTML5 canvas backend for browser and Juppyter viewing:

::

    a=imexam.connect(viewer='ginga')


Examples can be found in the package documentation, online documentation, and imexam.display_help() will pull up the installed package documentation in a web browser.


You can also just load the plotting library and NOT connect to any viewer:

::

    from imexam.imexamine import Imexamine
    import numpy as np

    plots = Imexamine()
    data = np.random.rand(100,100) * np.ones((100,100))
    plots.plot_line(35,45,data) #shows a matplotlib window with a plot
    plots.save() #saves the current plot to file
    

License
-------

imexam is licensed under a 3-clause BSD style license (see the
``licenses/LICENSE.rst`` file).

.. _AstroPy: http://www.astropy.org/
