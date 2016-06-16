:orphan:

======================
Updates to the package
======================


version 0.6dev (unreleased)
---------------------------
- Ginga viewer support for images in matplotlib and QT backend removed, but replaced with HTML5 canvas viewer which is faster and simpler for users to both use and install.
- replaced custom fits with astropy.modeling, enabling Gaussian2d, Gaussian1d, Moffat1D and MexicanHat1D fits for lines and centering
- General bug fixes and documentation updates, including example jupyter notebooks
- Updated the default title display on plots to use the image name or specify an array was used
- added astropy_helpers as a submodule
- made xpa a submodule
- if users pass an nddata object to view()  without a data reference it assumes one, but you can always specify which extension
- added better user access function for changing plotting/function parameters used to make plots


version 0.5.3dev (unreleased)
-----------------------------
- show with blocking deprecated in matplotlib, changed the calls to pause
- added a radial profile plot under the r key, the curve of growth plot was moved to g


version 0.5.2 (released)
------------------------
 - windows build change


version 0.5.1 (released)
------------------------
 - version upgraded needed for the release on pypi so it would accept the upload


version 0.5 (released)
----------------------

- Ginga viewer with matplotlib backend fully flushed out, this uses an event driven examination which is activated by key-press
- general bug fixes
- documentation updates


version 0.4dev (unreleased)
---------------------------

- Ginga is added as an optional viewer


version 0.3.dev (unreleased)
----------------------------
- Fixed bug where a user displayed array reference was not getting reset when a fits image was loaded into the frame instead
- added suggested changes from 2to3, and set use_2to3 to False
- restructured docs for astropy style and added more detailed example information
- general bugs fixed as they were found
- full support for arrays loaded from memory added
- restructured how the code tracks what is in the viewer. It used to track just the
  current frame, now it keeps a dictionary of what's loaded into the viewer which also
  contains some specifics about the data in each respective frame. This was necessary to
  allow user display and tracking of arrays, but also is a nicer way to store the information
  and give users access to more details about the viewer in general if they are scripting something
  themselves.
- the logging method dropped a reference in one of the last commits, this was fixed and logging the
  session to a file for reference should be functioning correctly again.
- fixed an internal tracking problem in cases where the user loaded files through the gui and then
  immediately issued the imexam() command. The viewer information for the object had not been updated in
  between because it waits for a call to the window before checking - I added this check to the top of
  imexam function.

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
