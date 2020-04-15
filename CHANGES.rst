version 0.9.2.dev (unreleased)
------------------------------


version 0.9.1 (2020-03-30)
--------------------------
- updated classifiers in pypi
- cleanup of branch

version 0.9 (2020-03-30)
---------------------------
- moved extension local to imexam 
- cleanup of travis tests and general package reorg
- renamed xpa extension for compatibility and updated to version 2.1.19
- added option for center of mass to aperature photometry centering
- update aper_phot to return tuple of photometry information without plotting
- optional error array can be sent to aper_phot when using without plotting
- updated example jupyter notebooks to be compatible with current functionality
- changed the ext_build process a little and added a flag to skip remaking the c code
- remove leftover iraf variable names
- removed support for the grab function under Darwin
- add deleted import of xpa back to utils (#192)
- adapt for change to photutils API for aperture areas (#193)
- fix ginga display of HDUList
- add check for ds9 in alias as well as well as path
- python2->3 class and printing updates
- removed dependence on astropy_helpers

version 0.8.1 (2018-12-14)
--------------------------
** THIS WILL BE THE LAST VERSION THAT SUPPORT Python 2.7 **

- travis and appveyor testing updates
- radial profile plot centering fixed to more correctly calculate the fractional center offsets
- cumulative radial profile flux calculation should now be correct
- the fit_gauss_1d function call was changed to accept the radius and flux array so that they
  could be constructed correctly for multiple circumstances 
- documentation updated and new simple walkthrough added
- MEF fits images with IMAGE arrays in the primary HDU should be detected correctly now
- now possible to give load_fits an in-memory fits object
- code cleanup and minor bug fixes
- background fit added to 1D and 2D Gaussian fits
- plotting AiryDisk2D fit is now possible
- unit test updates
- new options added to the aperture phot parameter set that allow users to plot the used apertures
- ZScaleInterval added from astropy.virtualization to set the color range on the data for aperture photometry plot
- replaced the sigma to fwhm lambda with the astropy constant for conversion
- added cursor move recognition using the arrow keys during the imexam loop, however, depending how the user has their windowing focus set, the DS9 window may loose focus, forcing them to move the cursor manually back to the window. Cursor moves are only implemented for DS9, not Ginga.

version 0.8.0 (2017-11-06)
--------------------------
- fixed show_xpa_commands bug sending None instead of empty string
  to the xpa library
- fixed logic of connect method. When a target is given, do not look
  for an executable
- view method now supports loading cubes when there are 3 dimension in the given array
- logic bug in ds9 class init updated to warn when user specified target doesn't exist

  
version 0.7.1 (2017-02-06)
--------------------------
- fixed xpa bug holdout from updating for windows specific code
- changed default connection type from local to inet when XPA_METHOD not specified in users environment


version 0.7.0 (2017-01-19)
--------------------------
- fixed a text error in the display_help() so that now the correct version loads the documentation
- Windows users can now install from source. The setup will ignore the cython and xpa necessary to build the DS9 interaction, and users will only be able to use the Ginga HTML5 window, they can also use the Imexamine() functions without any graphical interface.
- Documentation updates, mostly specific information for Windows users
- Added python 3.6 to the test matrix as well as apveyor for the windows build
- Updated XPA module to v2.1.18
- Made fits checker smarter to deal with older simple fits files where EXTEND is true but there are no extensions
- fixed bug in fits loader for ds9 multi-extension FITS files, made load_fits() prefer the extension specified in the key rather than the image name



version 0.6.4dev (unreleased)
-----------------------------
- fixed a text error in the display_help() so that now the correct version loads the documentation
- Windows users can now install from source. The setup will ignore the cython and xpa necessary to build the DS9 interaction, and users will only be able to use the Ginga HTML5 window, they can also use the Imexamine() functions without any graphical interface.
- Documentation updates, mostly specific information for Windows users
- Added python 3.6 to the test matrix as well as apveyor for the windows build
- Updated XPA module to v2.1.18
- Made fits checker smarter to deal with older simple fits files where EXTEND is true but there are no extensions
- fixed bug in fits loader for ds9 multi-extension FITS files, made load_fits() prefer the extension specified in the key rather than the image name


version 0.6.3 (2017-01-01)
--------------------------
- Logging was updated to fix bugs as well allow for more user control of the log files. Additionally, most prints were moved to the stdout stream handler so that users could also shut off messages to the screen
- The imexamine class was updated so that analysis functions could be more easily called by external entities. This was primarily to support ginga plugins, and a new imexam plugin for ginga.
- A dictionary is now returned to the user when they request information on the active DS9 windows which are available.
- Tests updated to be consistent with new package logging
- Documentation and the jupyter examples updated
- Fixed bug with loading user specified fits extensions for both ginga and ds9


version 0.6.2 (2016-08-10)
--------------------------
- Unbinned radial plots were added, bins are still an available option
- documentation updates


version 0.6.1 (2016-07-16)
--------------------------
- Ginga viewer support for images in matplotlib and QT backend removed, but replaced with HTML5 canvas viewer which is faster and simpler for users to both use and install.
- replaced custom fits with astropy.modeling, enabling Gaussian2d, Gaussian1d, Moffat1D and MexicanHat1D fits for lines and centering
- General bug fixes and documentation updates, including example jupyter notebooks
- Updated the default title display on plots to use the image name or specify an array was used
- added astropy_helpers as a submodule
- made xpa a submodule
- if users pass an nddata object to view()  without a data reference it assumes one, but you can always specify which extension
- added better user access function for changing plotting/function parameters used to make plots
- updated to Read The Docs new site name
- replaced ipython dependency in the docs build with jupyter
- removed local copy of doc build, referenced to RTD instead, users should make PDF copy for offline work
- added the ginga embed functionality so that users can choose to embed the viewing window inside the notebook

version 0.5.3dev (unreleased)
-----------------------------
- show with blocking deprecatedin matplotlib, changed the calls to pause
- added a radial profile plot under the r key, the curve of growth plot was moved to g


version 0.5.2 (2016-01-29)
--------------------------
 - windows build change


version 0.5.1 (2016-01-29)
--------------------------
 - version upgraded needed for the release on pypi so it would accept the upload


version 0.5 (2015-05-01)
------------------------

- Ginga viewer with matplotlib backend fully flushed out,
this uses an event driven examination which is activated by key-press

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

- full imexam() support for arrays loaded from memory added

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
