Example 1
=========

Basic Usage
-----------

First you need to import the package
::

    import imexam

Start up a DS9 window (by default), a new DS9 window will be opened
::

    a=imexam.connect()

If you already have a window running, you can ask for a list of windows
::

    imexam.list_active_ds9()
    DS9 ds9 gs 82a7e75f:57222 sosey


You can attach to a current DS9 window be specifying its unique name
::

    a=imexam.connect('ds9')  


If you haven't given your windows unique names, then you must use the ip:port address
::

    a=imexam.connect('82a7e75f:57222')


Load a fits image into the window
::

    a.load_fits('test.fits')

Scale to default using zscale
::

    a.scale()

Change to heat map colorscheme
::

    a.cmap(color='heat')

Make some marks on the image and save the regions
::

    a.save_regions('test.reg')

Delete all the regions you made, then load from file
::

    a.load_regions('test.reg')

Plot stuff at cursor location, in a while loop. Type a key when the mouse is over your desired location and continue plotting with the available options
::

    a.imexam()
    
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

    a.close()

