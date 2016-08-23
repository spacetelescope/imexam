:orphan:

=========
Example 1
=========

Basic Usage
-----------

First you need to import the package
::

    import imexam


Usage with D9 (the current default viewer)
------------------------------------------

Start up a DS9 window (by default), a new DS9 window will be opened
::

    viewer=imexam.connect()

If you already have a window running, you can ask for a list of windows; windows that you start from the imexam package will not show up, this is to keep control over their processes and prevent double assignments.

::

    imexam.list_active_ds9()
    DS9 ds9 gs 82a7e75f:57222 sosey


You can attach to a current DS9 window be specifying its unique name
::

    viewer=imexam.connect('ds9')


If you haven't given your windows unique names, then you must use the ip:port address
::

    viewer=imexam.connect('82a7e75f:57222')



Usage with Ginga viewer
-----------------------

Start up a ginga window using the HTML5 backend. Make sure that you have installed the most recent version of ginga, imexam will return an error that the viewer cannot be found otherwise.


::

    viewer=imexam.connect(viewer='ginga')



All commands after your chosen viewer is opened are the same
-------------------------------------------------------------

Load a fits image into the window
::

    viewer.load_fits('test.fits')

Scale the image to the default scaling, which uses zscale
::

    viewer.scale() <-- uses zscale
    viewer.scale('asinh')  <-- uses asinh

Change to heat map colorscheme
::

    viewer.cmap(color='heat')


Make some marks on the image and save the regions using a DS9 style regions file
::

    viewer.save_regions('test.reg')

Delete all the regions you made, then load from file
::

    viewer.load_regions('test.reg')

Plot stuff at the cursor location, in a while loop. Type a key when the mouse is over your desired location and continue plotting with the available options
::

    viewer.imexam()

     'a': 'aperture sum, with radius region_size, optional sky subtraction',
     'j': '1D  line fit ',
     'k': '1D  column fit ',
     'm': 'median square region stats, in region_size square',
     'n': 'move to the next frame',
     'p': 'move to the previous frame',
     'x': 'return x,y coords of pixel',
     'y': 'return x,y coords of pixel',
     'l': 'return line plot',
     'c': 'return column plot',
     'r': 'return curve of growth plot',
     'h': 'return a histogram in the region around the cursor'
     'e': 'return a contour plot in a region around the cursor'
     's': 'save current figure to plotname'
     'b': 'return the gauss fit center of the object'
     'w': 'display a surface plot around the cursor location'


Quit out and delete windows and references
::

    viewer.close()
