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


Starting a connection to a Ginga widget, using the Matplotlib backend for viewing:

::

    a=imexam.connect(viewer='ginga_mp')


Examples can be found in the package documentation, online documentation, and imexam.display_help() will pull up the installed package documentation in a web browser.


License
-------

imexam is licensed under a 3-clause BSD style license (see the
``licenses/LICENSE.rst`` file).

.. _AstroPy: http://www.astropy.org/
