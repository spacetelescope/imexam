=======================================
Convenience functions for  XPA commands
=======================================

.. note:: The full list of XPA access points can be found at: http://ds9.si.edu/doc/ref/xpa.html and XPA itself is maintained here https://github.com/ericmandel/xpa

    If there is no convenience function for an access point that you would like to use,  you can still call it using the ``imexam`` hooks into the xpa GET and SET functions. They are aliased to your object (for example "window") as window.window.xpa.get() or window.window.xpa.set()


**alignwcs** (on=True):
    align loaded images by wcs,

**blink** (blink=None,interval=None):
    blink frames

**clear_contour** ():
    clear contours from the screen

**cmap** (color=None,load=None,invert=False,save=False, filename='colormap.ds9'):
    set the color map of the current frame
    The available maps are "heat","grey","cool","aips0","a","b","bb","he","i8"

    color: string
        color must be set to one of the available DS9 color map names

    load: string, optional
        set to the filename which is a valid colormap lookup table
        valid contrast values are from 0 to 10, and valid bias values are from 0 to 1

    invert: bool, optional
        invert the colormap

    save: bool, optional
        save the current colormap as a file

    filename: string, optional
        the name of the file to save the colormap to


**colorbar** (on=True):
    turn the colorbar at the bottom of the screen on and off

**contour** (on=True, construct=True):
        on: Set to true to turn on contours

        construct: optional
            Will open the contour dialog box which has more options

**contour_load** (filename):
    load contours into the window from the specified filename

**crosshair** (x=none,y=none,coordsys="physical",skyframe="wcs",skyformat="fk5",match=False,lock=False):
    control the current position of the crosshair in the current frame, crosshair mode is turned on

    x: string or int
        The value of x is converted to a string for the call to XPA, use a value here appropriate for the skyformat you choose

    y: string or int
        The value of y is converted to a string for the call to XPA, use a value here appropriate for the skyformat you choose

    coordsys: string, optional
        The coordinate system your x and y are defined in

    skyframe: string, optional
        If skyframe has "wcs" in it then skyformat is also sent to the XPA

    skyformat: string, optional
        Used with skyframe, specifies the format of the coordinate which were given in x and y

    match: bool, optional
        If set to True, then the wcs is matched for the frames

    lock: bool, optional
        If set to True, then the frame is locked in wcs

**cursor** (x=None,y=None):
    move the cursor in the current frame to the specified image pixel, it will also move selected regions

**disp_header** ():
    display the current header using the ds9 header display window

**frame** (n=None):
    convenience function to switch frames or load a new frame (if that number does not already exist)

    n: int, string, optional
        The frame number to open or change to. If the number specified doesn't exist, a new frame will be opened
        If nothing is specified, then the current frame number will be returned. The value of n is converted to
        a string before passing to the XPA

    frame(1)  sets the current frame to 1
    frame("last") set the current frame to the last frame
    frame() returns the number of the current frame
    frame("new") opens a new frame
    frame(3)  opens frame 3 if it doesn't exist already, otherwise goes to frame 3


**get_header** ():
    return the header of the current extension as a string, or None if there's a problem

**grid** (on=True, param=False):
    turn the grid on and off
    if param is True, then a diaglog is opened for the grid parameters

**hideme** ():
    lower the ds9 window on your display

**load_fits** (fname=None, extname=1, extver='SCI'):
    load a fits image to the current frame. You provide just the name, or either of the extname or extver, or you
    can specify the extension with the filename string. For example:

        load_fits('something.fits',extver='SCI')  will load the SCI,1 extension

        load_fits('something.fits[SCI,1]') will load the SCI,1 extension

        load_fits('something.fits') will load the main data extension; the only data information in the case of simple fits, or the first extension in the case of a multiextension file

**load_region** (filename):
    load the specified DS9 formatted region filename

**load_rgb** (red, green, blue,scale=False, lockwcs=False):
    load 3 images into an RGBimage frame, the parameters are::

        red: string, The name of the fits file which will be loaded into the red channel

        green: string, The name of the fits file which will be loaded into the green channel

        blue: string, The name of the fits file which will be loaded into the blue channel

        scale: bool, If True, then each image will be scale with zscale() after loading

        lockwcs: bool, If True, then the image positions will be locked to each other using the WCS information in their headers

**load_mef_as_cube** (filename=None):
    Load a Mult-Extension-Fits image into one frame as an image cube in the image viewer

**load_mef_as_multi** (filename=None):
    Load a Mult-Extension-Fits image into multiple frames in the image viewer


**match** (coordsys="physical",frame=False,crop=False,fslice=False,scale=False,bin=False,colorbar=False,smooth=False,crosshair=False):
    match all other frames to the current frame using the specified option. You can only choose one of the options at a time, so set frame=False and something else in addition to your choice if you don't want the default option.

    coordsys: string, optional
        The coordinate system to use

    frame: bool, optional
        Match all other frames to the current frame, using the set coordsys

    crop: bool, optional
        Set the current image display area, using the set coordsys

    fslice: bool, optional
        Match current slice in all frames

    scale: bool, optional
        Match to the current scale for all frames

    bin: bool, optional
        Match to the current binning for all frames

    colorbar: bool, optional
        Match to the current colorbar for all frames

    smooth: bool, optional
        Match to the current smoothing for all frames

    crosshair: bool, optional
        Match the crosshair in all frames, using the current coordsys


**nancolor** (color="red"):
    set the not-a-number color, default is red

**panto_image** (x, y)
    convenience function to change to x,y images coordinates using ra,dec

**panto_wcs** (x, y,system='fk5'):
    pan to the wcs coordinates in the image using the specified system

    x: string
        The x location to move to, specified using the given system
    y: string
        The y location to move to
    system: string
        The reference system that x and y were specified in, they should be understood by DS9


**rotate** (value, to=False):
    value: float [degrees]
        Rotate the current frame {value} degrees
        If value is 0, then the current rotation is printed

    to: bool
        Rotate the current frame to the specified value instead

**save_header** (filename=None):
    save the header of the current image to a file


**save_rgb** (filename=None):
    save an rgbimage frame as an MEF fits file

**save_regions** (filename=None):
    Save the regions in the current window to a DS9 style regions file

    filename: string
        The nameof th file to which the regions displayed in the current window are saved
        If no filename is provided then it will try and save the regions to the name of the
        file in the current display with _regions.txt appended

        If a file of that name already exists on disk it will no attempt to overwrite it


**scale** (scale='zscale'):
    Scale the image on display. The default zscale is the most widely used option::

          Syntax

          scales available: [linear|log|pow|sqrt|squared|asinh|sinh|histequ]

          [log exp <value>]
          [datasec yes|no]
          [limits <minvalue> <maxvalue>]
          [mode minmax|<value>|zscale|zmax]
          [scope local|global]
          [match]
          [lock [yes|no]]
          [open|close]

**set_region** (region_string):
    display a region using the specifications in region_string
    example: set_region("physical; ruler 200 300 200 400")

**showme** ():
    raise the ds9 display window

**showpix** ():
    display the pixel value table

**snapsave** (filename,format=None,resolution=100):
    create a snap shot of the current window and save in specified format. If no format is specified the filename extension is used

       filename: str, optioan
           filename of output image, the extension in the filename can also be used to specify the format
           If no filename is specified, then the filename will be constructed from the name of the
           currently displayed image with _snap.jpg appended.

       format: str, optional
           available formats are fits, eps, gif, tiff, jpeg, png
           If no format is specified the filename extension is used

       resolution: int, optional
           1 to 100, for jpeg images

**zoom** (par="to fit"):
    par: string
        it can be a number (ranging 0.1 to 8), and successive calls continue zooming in the same direction
        it can be two numbers '4 2', which specify zoom on different axis
        if can be to a specific value 'to 8' or 'to fit', "to fit" is the default
        it can be 'open' to open the dialog box
        it can be 'close' to close the dialog box (only valid if the box is already open)

**zoomtofit** ():
    zoom to the best fit for the display window
