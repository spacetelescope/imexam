============================================================
Convenience functions for some of the available XPA commands
============================================================

.. note:: The full list of XPA access points can be found at: http://ds9.si.edu/doc/ref/xpa.html

    If there is no convenience function for an access point that you would like to use,  you can still call it using the imexam hooks into the xpa GET and SET functions. They are aliased to your object (for example "window") as window.get() or window.set()


alignwcs(on=True): 
    align loaded images by wcs, 

blink(blink=None,interval=None): 
    blink frames

clear_contour():
    clear contours from the screen
    
cmap(color=None,load=None,invert=None,lock=None): 
    set the color map of the current frame to something else. 
    
    The available maps are "heat","grey","cool","aips0","a","b","bb","he","i8"

colorbar(on=True):
    turn the colorbar at the bottom of the screen on and off
    
contour(on=True, construct=True):
    show contours on the window. If construct is True, then the contour dialog box will open
    
contour_load(filename):
    load contours into the window from the specified filename
    
crosshair(x=none,y=none,coordsys="physical",skyframe="wcs",skyformat="fk5",match=False,lock=False):
    control the current position of the crosshair in the current frame, crosshair mode is turned on
    If match is True, wcs matching is used
    If lock is True, wcs lock is used
    
cursor(x=None,y=None):
    move the cursor in the current frame to the specified image pixel, it will also move selected regions

disp_header(ext=None):
    display the current header using the ds9 header display window

frame(n=None): 
    convenience function to switch frames or load a new frame (if that number does not already exist)

get_header(ext=None):
    return the header of the current extension as a string

grid(on=True, param=False): 
    turn the grid on and off
    if param is True, then a diaglog is opened for the grid parameters

hideme():
    lower the ds9 window
    
load_fits(fname=None, ext=1): 
    load a fits image to the current frame

load_region(filename): 
    load the specified DS9 formatted region filename

match(coordsys="physical",frame=False,crop=False,fslice=False,scale=False,bin=False,colorbar=False,smooth=False,crosshair=False):
    match all other frames to the current frame
    
nancolor(color="red"):
    set the not-a-number color, default is red

save_header(filename=None):
    save the header of the current image to a file
 
save_regions(filename): 
    save the regions in the current window frame to filename

panto_image(x, y)
    convenience function to change to x,y images coordinates using ra,dec
    
panto_wcs(x, y,system='fk5'): 
    pan to the wcs coordinates in the image using the specified system

save_header(ext=None,filename=None): 
    save the header of the current frame image to a file

scale(scale='zscale'): 
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

set_region(region_string):
    display a region using the specifications in region_string
    
showme():
    raise the ds9 display window
    
showpix():
    display the pixel value table

snapsave(self,filename,format=None,resolution=100):
    create a snap shot of the current window and save in specified format. If no format is specified the filename extension is used

zoom(par="to fit"): 
    par can be a number, to fit, open or close

zoomtofit(): 
    zoom to the best fit for the display window






    


