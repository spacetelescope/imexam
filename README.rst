imexam
======

imexam is meant as a replacement for the IRAF imexamine task. You should be able to perform all of the important functions that imexamine provided using DS9 as your display device and through a python session.

For more information please see the `online documentation <http://imexam.readthedocs.org/>`_


Some code in this package was adapted from pysao, which can be found at http://leejjoon.github.com/pysao/, which is licensed under the MIT and AURA general licenses, included with this package.
Specifically this package used the existing Cython implementation to the XPA  and extended the calls to the other available XPA executables so that more functionality is added. 
Using Cython will allow for broader development of the code and produce faster runtimes for large datasets with repeated calls to the display manager.


XPA is licensed under LGPL, help can be found here: http://hea-www.cfa.harvard.edu/saord/xpa/help.html 
The current XPA can be downloaded from here: http://hea-www.harvard.edu/saord/xpa/

ds9 also supports the SAMP protocol, but that has not been fully implemented in this package. http://ds9.si.edu/doc/ref/samp.html


Launching multiple DS9 windows
------------------------------

You can launch multiple ds9 windows either from this package or the command line. 
If you launch ds9 from outside the imexam package, you need supply the name of the window to imexam, this can be done in one of 2 ways:

* launch ds9 with a unique title name:    

::
    
    ds9 -title megan&   

then supply imexam the name of the window:

::

    a=imexam.ds9(target='megan')

* launch ds9 with nothing:   

::
    
    ds9&  

then supply imexam with the XPA_METHOD from the XPA information window: 

::

    a=imexam.connect(target='82a7e674:51763')


Examples can be found in the package documentation, online documentation, and imexam.display_help() will pull up the installed package documentation in a web browser.
