*********************
Software Dependencies
*********************

*   Astropy (for some analysis functions)
*   photutils (for photometry)
*   matplotlib (for plotting)
*   DS9 (for image display) 

astropy >= 1.0

python >= 2.7
Python 2.6 and 3.2 are not currently supported

numpy >= 1.6.0

photutils > 0.2dev
    This must be installed to enable the photometry options for imexam() but it is not required

scipy.optimize.curve_fit


Ginga
    This must be installed in order to use the Ginga displays instead of DS9. Using ginga has the advantage that the imexam() loop is now event driven. Issuing the command:
    
        viewer.imexam()
        
        
Will print out the available examination command keys. The user can then press the "i" key while the mouse is in the graphics window, all subsequent key-presses will be grabbed without blocking your terminal command line. If you wish to turn of the imexam keys you can press either the "i" key a second time or the "q" key. A notification message will appear on screent that imexam mode has either started or stopped.


