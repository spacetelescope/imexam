************
Introduction
************

imexam is meant as a replacement for the IRAF imexamine task. You should be able to perform all of the important functions that imexamine provided using DS9 as your display device and through a python session.

It communicates with the DS9 window, either one you already have open, or one that imexam explicitly opens, through the XPA messaging system. 

You can access this help file on your locally installed copy of the package by using the imexam.display_help() call, which will display the help in your web browser.

All returned information should be considered an estimate of the actual refined result,  more precise analysis of the data should be performed for verification before publication.  


Usage
=====

imexam is a class based library. The user creates an object which is tied to a specific image viewing program, such as DS9. In order to interact with multiple  windows the user must create multiple objects. Each object stores all the relevent information about the window and data with which it is associated. For example, in order to open a new DS9 window and use the object "window" to control it, you would issue the commmand:

::
    
    window=imexam.connect()
    
"window" now has associated methods to view, manipulate and analyze data in the DS9 session. When you start the connection, you also have the option of specifying a currently open DS9 window using the target keyword. This keyword can contain the name, the actual text name that you gave the window, or the address of the window. 

The address of the window can be found in the File->XPA->Information menu item,  is stored as "XPA_METHOD", and is of the form "82a7e75f:58576" for inet sockets. 

::

    window=imexam.connect("82a7e75f:58576")
    
    
When imexam starts up a DS9 window itself, it will create an inet socket, which is also the default connection type for DS9. If you are experiencing problems, or you don't have an internet connection (the two might be related because the XPA structures inet sockets with an ip address), you can set your environment variable XPA_METHOD to 'local' or 'localhost'. This will cause imexam to start a local(unix) socket which will show an "XPA_METHOD" that is a filename on your computer. 


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


More detailed examples can be found in the examples section.


.. note:: More information on DS9 can be found at: http://ds9.si.edu/site/Home.html


.. include:: iraf_imexam.rst

.. include:: comparison_iraf.rst
