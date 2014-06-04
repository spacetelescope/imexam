
IRAF imexamine capabilities
===========================

These are the capabilities of the IRAF version of the imexam task, called with **imexamine [input [frame]]**, which lives in images.tv.imexamine. The following are imexamines input options:


    *  **input** is an optional list of images to be examined. If specified, images are examined in turn, displaying them automatically. If no images are specfied the images currently loaded into the image display are examined.
    
    *   **output** contains the rootname for output images created with the "t" key. If no name is specified then the name of the input image is used. A three digit numver is appended to the rootname, such as ".001", starting with 1 until no image is found with that name. Successive output images are numbered sequentially
    
    *   **ncoutput** and **nloutput** are the size of the output image created when the "t" key is pressed, where the output image is centered on the cursor location
    
    *   **frame** specifies which frame should be used
    
    *   **logfile** is the filename which records output of the commands producing text, if no filename is given no logfile will be produced
    
    *   **defkey** is the default key for cursor x-y input list. This key is applied to input cursor lists which do not have a cursor key specified. It is used to repetitively apply a cursor command to a list of positions typically obtained from another task
    
    *   **allframes**, if true then images from an input list are loaded by cycling through the available frames, otherwise the last frame loaded is reused
    
    *   **nframes** is then number of display frames to use when automatically loading images. It should not exceed the number of frames provided by the display device.  If the number of frames is set to 0 then the task will query the display  device  to  determine how  many  frames  are  currently  allocated.  New frames may be allocated during program execution  by  displaying  images  with the 'd' key.

    *   **ncstat, nlstat** correlate with the statistics command which computes values from a box centered on the specified cursor position with the number of columns and lines given by these parameters.


The following is a list of available cursor and colon commands while imexamine is active in the display, many but not all are available in this python imexam package:

.. literalinclude:: iraf_commands.txt
 
