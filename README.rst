imexam
======

imexam is meant as a replacement for the IRAF imexamine task. You should be able to perform all of the important functions that imexamine provided using DS9 or a Ginga widget as your display device through a python session.

For more information please see the `online documentation <http://imexam.readthedocs.org/en/latest/imexam/index.html>`_


To install using pip:

::

    pip install imexam
    
    
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

