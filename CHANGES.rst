version 0.2.dev (unreleased)
----------------------------

- zero-indexing bug fixed for data pixel display

- added support for x-D image cubes. They display, and are correctly tracked through
  the imexam loop. Several new functions were added to support this.
  
- fixed the zoom(int) bug, you can supply an int or string to the zoom function and it will be happy



version 0.1.dev (unreleased)
----------------------------

This update should address all of the issues that chanley raised,, including:

- Removing the remaining blind exceptions

- Removing unused imports

- Setting an appropriate default value for the connect.current_frame

  - the code now calls to the active window to set the frame

  - I also updated related ds9 module frame method to set the frame to a decent default if not set

- the astropy.io.fits import was simplified

- In addition, some minor typos and bugs were fixed that appeared when making these updates.
