=====================
Software Dependencies
=====================

*   Astropy (for some analysis functions)
*   photutils (for photometry)
*   matplotlib (for plotting)
*   DS9 (image display - optional)
    * XPA: https://github.com/ericmandel/xpa
*   Ginga (image display - optional )

astropy >= 1.0

python >= 2.7

numpy >= 1.6.0

photutils > 0.2dev
    This must be installed to enable the photometry options for imexam() but
    it is not required


Ginga
    This must be installed in order to use the Ginga displays instead of DS9.
    Using ginga has the advantage that the imexam() loop is now event driven.

    You can issue the viewer.imexam() command to print out the available
    examination command keys. The user can then press the "i" key while
    the mouse is in the graphics window, all subsequent key-presses will be
    grabbed without blocking your terminal command line. If you wish to turn
    of the imexam keys you can press either the "i" key a second time or the
    "q" key. A notification message will appear on screen that imexam mode
    has either started or stopped.

    If you are using the Ginga HTML5 widget under python3 in the Jupyter notebook
    you should also install Pillow to get the correct image viewing
