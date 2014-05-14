************
Introduction
************

imexam is meant as a replacement for the IRAF imexamine task. You should be able to perform all of the important functions that imexamine provided in IRAF, but you also gain the power and flexibility of python and matplotlib. 

It currently provides display support with a DS9 window, either one you already have open, or one that imexam explicitly opens, and communicates through the XPA messaging system. The module is designed to accept other display devices in the future (for example Ginga)

.. note:: It is important to know if you have XPANS installed on your machine and available through your PATH. XPANS is the XPA Name Server, it keeps track of all the open socket connections for DS9 and provides a reference for their names. If you DO NOT have XPANS installed, then imexam will still work, but you should either start the DS9 window after importing imexam through the imexam.connect() interface, OR after you start DS9 from the shell, make note of the XPA_METHOD address in the File->Information dialog and use that in your call to connect: window=imexam.connect(XPA_METHOD) so that communication with the correct socket is established. As a convenience, a full installation of the XPA software is packaged with this module, and the XPANS executable is compiled upon installation. You may choose whether or not to make use of this.


You can access this help file on your locally installed copy of the package by using the imexam.display_help() call, which will display the help in your web browser.

.. note:: All information returned from this module should be considered an estimate of the actual refined result,  more precise analysis of the data should be performed for verification before publication.  


Usage
=====

imexam is a class based library. The user creates an object which is tied to a specific image viewing window, such as a DS9 window. In order to interact with multiple  windows the user must create multiple objects. Each object stores all the relevent information about the window and data with which it is associated. For example, in order to open a new DS9 window and use the object "window" to control it, you would issue the commmand:

::
    
    window=imexam.connect()
    
"window" now has associated methods to view, manipulate and analyze data in the DS9 session. When you start the connection, you also have the option of specifying a currently open DS9 window using the target keyword. This keyword can contain the name, the actual text name that you gave the window, or the address of the window. 

The address of the window can be found in the File->XPA->Information menu item,  is stored as "XPA_METHOD", and is of the form "82a7e75f:58576" for inet sockets, and a filepath for local sockets.

::

    window=imexam.connect("82a7e75f:58576")
    
    
When imexam starts up a DS9 window itself, it will create a local socket by default,  the default connection type for DS9 is inet. However, imexam will first check to see if XPA_METHOD was set in your environment and default to that option. If you are experiencing problems, or you don't have an internet connection (the two might be related because the XPA structures inet sockets with an ip address), you can set your environment variable XPA_METHOD to 'local' or 'localhost'. This will cause imexam to start a local(unix) socket which will show an "XPA_METHOD" that is a filename on your computer. imexam defaults to a local socket connection to allow for users who do not have the XPA installed on their machine or available on their PATH. The full XPA source code is installed with the imexam package, and the xpans executable is copied to the scripts directory of your local installation. If you don't have the XPA on your path, simply point it to that location, or copy xpans to the location of your choice, and make sure you update your PATH. Any time DS9 is started it will start up the xpa nameserver automatically. Then all the xpans query options will be available through imexam.  imexam itself uses cython wrappers around the get and set methods from the XPA for it's communication which is why the fully installed XPA is not needed.

If you wish to open multiple DS9 windows outside of imexam, then it's recommended that you give each a unique name. If you've forgotten which window had which name, you can look in the same XPA info menu and use the "XPA_NAME" specified there. If you haven't given them a unique name, you can list the available windows using imexam.list_active_ds9() and specify their unique address. 

imexam will attempt to find the current location of the DS9 executable by default, but you may also supply the path to the DS9 executable of your choice using the path keyword. The fully optional calling sequence is:  


:: 
       
    imexam.connect(target="",path=None,viewer="ds9",wait_time=10)


In order to return a list of the current DS9 windows that are running, issue the command:  

::

    imexam.list_active_ds9()

In order to turn logging to a file on, issue the command: window.setlog(). The log will be saved to the default filename imexam_session.log in the current directory unless you give it another filename to use.
Here's an example of how that might work:

::

    import imexam
    window=imexam.connect('ds9')
    window.setlog() <-- turns on logging with default filename
    window.imexam() <-- all output will be logged to the file and displayed on the screen
    window.setlog(on=False) <-- turns off logging to file
    window.setlog(filename='my_other_log.txt') <-- turns on logging and sets the save filename
    
    
The log will look something like this, you can see it contains a mention of the command used along with the results

::

    gauss_center 
    xc=812.984250   yc=706.562612

    aper_phot 
    x       y       radius  flux    mag(zpt=25.00)  sky     fwhm
    812.98  706.56  5       1288669.29      9.72    11414.53        4.83

    show_xy_coords 
    813.5 706.625

    gauss_center 
    xc=812.984250   yc=706.562612

    gauss_center 
    xc=239.856464   yc=233.444783

    aper_phot 
    x       y       radius  flux    mag(zpt=25.00)  sky     fwhm
    239.86  233.44  5       126601.26       12.24   11574.32        -12.67

    show_xy_coords 
    253.0 234.75

    gauss_center 
    xc=239.856464   yc=233.444783


More detailed examples can be found in the examples section of this documentation.


.. note:: More information on DS9 can be found at: http://ds9.si.edu/site/Home.html


.. include:: iraf_imexam.rst

.. include:: comparison_iraf.rst
