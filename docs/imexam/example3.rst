
=========
Example 3
=========

Advanced Usage - Interact with Daophot and Astropy
--------------------------------------------------
While the original intent for the imexam module was to replicate the realtime interaction of the old IRAF imexamine interface with data, there are other possibilities for data analysis which this module can support.One such example, performing more advanced interaction which can be scripted, is outlined below, using familiar IRAF tasks.

.. note:: You can see a similar photometry example which uses ``photutils`` and it's implementation of DAOPhot aperture photometry instead of IRAF in the `imexam_ds9_photometry example jupyter notebook. <https://github.com/spacetelescope/imexam/blob/master/example_notebooks/imexam_ds9_photometry.ipynb>`_

If you have  a  list of source identifications, perhaps prepared by SExtractor, DAOFind, Starfind or a similar program, you can use ``imexam`` to display the science image and overlay apertures for all their locations. From there you can do some visual examination and cleaning up of the list with a combination of region manipulation and useful ``imexam`` methods.

Here's our example image to work with, which is a subsection of a larger image:

.. image:: ../_static/simple_ds9_open.png
        :height: 600
        :width: 400
        :alt: imexam with DS9 window and loaded fits image


I'll use the IRAF DAOFind to find objects in my field:

::


    from pyraf import iraf
    from iraf import noao,digiphot,daophot
    from astropy.io import fits

    image='iabf01bzq_flt.fits'

    fits.info('iabf01bzq_flt.fits')

        Filename: iabf01bzq_flt.fits
        No.    Name         Type      Cards   Dimensions   Format
        0    PRIMARY     PrimaryHDU     210   ()           int16
        1    SCI         ImageHDU        81   (1014, 1014)   float32
        2    ERR         ImageHDU        43   (1014, 1014)   float32
        3    DQ          ImageHDU        35   (1014, 1014)   int16
        4    SAMP        ImageHDU        30   ()           int16
        5    TIME        ImageHDU        30   ()           float32



    #set up some finding parameters, you can make this more explicit
    iraf.daophot.findpars.threshold=3.0 #3sigma detections only
    iraf.daophot.findpars.nsigma=1.5 #width of convolution kernal in sigma
    iraf.daophot.findpars.ratio=1.0 #ratio of gaussian axes
    iraf.daophot.findpars.theta=0.
    iraf.daophot.findpars.sharplo=0.2 #lower bound on feature
    iraf.daophot.findpars.sharphi=1.0 #upper bound on feature
    iraf.daophot.findpars.roundlo=-1.0 #lower bound on roundness
    iraf.daophot.findpars.roundhi=1.0 #upper bound on roundness
    iraf.daophot.findpars.mkdetections="no"

        In [84]: iraf.lpar(iraf.daophot.datapars)
               (scale = 1.0)            Image scale in units per pixel
             (fwhmpsf = 2.5)            FWHM of the PSF in scale units
            (emission = yes)            Features are positive?
               (sigma = 1.0)            Standard deviation of background in counts
             (datamin = 0.0)            Minimum good data value
             (datamax = INDEF)          Maximum good data value
               (noise = "poisson")      Noise model
             (ccdread = "")             CCD readout noise image header keyword
                (gain = "ccdgain")      CCD gain image header keyword
           (readnoise = 2.0)            CCD readout noise in electrons
               (epadu = 1.0)            Gain in electrons per count
            (exposure = "exptime")      Exposure time image header keyword
             (airmass = "")             Airmass image header keyword
              (filter = "")             Filter image header keyword
             (obstime = "")             Time of observation image header keyword
               (itime = 1.0)            Exposure time
            (xairmass = INDEF)          Airmass
             (ifilter = "INDEF")        Filter
               (otime = "INDEF")        Time of observation
                (mode = "ql")

    iraf.daophot.datapars.datamin=0.
    iraf.daophot.datapars.gain="ccdgain"
    iraf.daophot.datapars.exposure="exptime"
    iraf.daophot.datapars.sigma=105.


    #assume the science extension and find some stars
    sci="[SCI,1]"
    output_locations='iabf01bzq_stars.dat'
    iraf.daofind(image=image+sci,output=output_locations,interactive="no",verify="no",verbose="no")

    #This is just the top of the file that daofind produced:

        In [24]: more iabf01bzq_stars.dat
        #K IRAF       = NOAO/IRAFV2.16          version    %-23s
        #K USER       = sosey                   name       %-23s
        #K HOST       = intimachay.stsci.edu    computer   %-23s
        #K DATE       = 2014-03-28              yyyy-mm-dd %-23s
        #K TIME       = 15:34:56                hh:mm:ss   %-23s
        #K PACKAGE    = apphot                  name       %-23s
        #K TASK       = daofind                 name       %-23s
        #
        #K SCALE      = 1.                      units      %-23.7g
        #K FWHMPSF    = 2.5                     scaleunit  %-23.7g
        #K EMISSION   = yes                     switch     %-23b
        #K DATAMIN    = 0.                      counts     %-23.7g
        #K DATAMAX    = INDEF                   counts     %-23.7g
        #K EXPOSURE   = exptime                 keyword    %-23s
        #K AIRMASS    = ""                      keyword    %-23s
        #K FILTER     = ""                      keyword    %-23s
        #K OBSTIME    = ""                      keyword    %-23s
        #
        #K NOISE      = poisson                 model      %-23s
        #K SIGMA      = 105.                    counts     %-23.7g
        #K GAIN       = ccdgain                 keyword    %-23s
        #K EPADU      = 2.5                     e-/adu     %-23.7g
        #K CCDREAD    = ""                      keyword    %-23s
        #K READNOISE  = 0.                      e-         %-23.7g
        #
        #K IMAGE      = iabf01bzq_flt.fits[SCI, imagename  %-23s
        #K FWHMPSF    = 2.5                     scaleunit  %-23.7g
        #K THRESHOLD  = 3.                      sigma      %-23.7g
        #K NSIGMA     = 2.                      sigma      %-23.7g
        #K RATIO      = 1.                      number     %-23.7g
        #K THETA      = 0.                      degrees    %-23.7g
        #
        #K SHARPLO    = 0.2                     number     %-23.7g
        #K SHARPHI    = 1.                      number     %-23.7g
        #K ROUNDLO    = -1.                     number     %-23.7g
        #K ROUNDHI    = 1.                      number     %-23.7g
        #
        #N XCENTER   YCENTER   MAG      SHARPNESS   SROUND      GROUND      ID         \
        #U pixels    pixels    #        #           #           #           #          \
        #F %-13.3f   %-10.3f   %-9.3f   %-12.3f     %-12.3f     %-12.3f     %-6d       \
        #
           194.694   2.357     -3.335   0.919       0.141       -0.004      1
           232.659   2.889     -1.208   0.768       0.572       -0.289      2
           237.782   2.925     -1.182   0.669       0.789       -0.971      3
           265.715   2.797     -1.395   0.976       -0.450      -0.669      4
           419.792   2.902     -3.045   0.925       -0.990      0.213       5
           424.566   3.081     -1.202   0.923       0.513       -0.555      6
           534.758   2.856     -1.341   0.659       -0.676      -0.302      7
           580.964   2.485     -1.326   0.821       -0.489      -0.752      8
           587.521   3.568     -1.282   0.911       -0.537      -0.119      9
           725.016   3.999     -1.103   0.714       -0.653      -0.490      10
           736.495   2.808     -1.345   0.710       -0.996      -0.730      11
           746.529   3.200     -0.868   0.303       -0.376      -0.682      12
           757.672   3.172     -1.527   0.420       0.271       0.211       13
           768.768   2.830     -1.321   0.741       -0.842      -0.252      14
           799.199   2.696     -2.096   0.926       0.476       -0.511      15
           807.575   2.445     -4.136   0.745       0.171       -0.131      16
           836.661   2.790     -1.482   0.709       0.205       0.636       17
           879.390   3.069     -1.018   0.549       -0.479      -0.495      18
           912.820   2.806     -1.414   0.576       0.504       0.109       19
           938.794   3.448     -1.731   0.997       -0.239      0.100       20
           17.713    2.731     -1.896   0.286       -0.947      -0.359      21
           48.757    2.755     -1.172   0.586       0.646       -0.543      22
           105.894   3.030     -1.700   0.321       -0.233      -0.006      23

Now we want to read in the file that Daofind produced and save the x,y and ID information.
I'm going to read the results using  astropy.io.ascii

::

    reader=ascii.Daophot()
    photfile=reader.read(output_locations)

    #some quick information on what we have now
    photfile.colnames

        ['XCENTER', 'YCENTER', 'MAG', 'SHARPNESS', 'SROUND', 'GROUND', 'ID']

    photfile.print()

        In [103]: photfile.pprint()
           XCENTER     YCENTER      MAG     SHARPNESS      SROUND       GROUND      ID
        ------------- ---------- --------- ------------ ------------ ------------ ------
        194.694       2.357      -3.335    0.919        0.141        -0.004       1
        232.659       2.889      -1.208    0.768        0.572        -0.289       2
        237.782       2.925      -1.182    0.669        0.789        -0.971       3
        265.715       2.797      -1.395    0.976        -0.450       -0.669       4
        419.792       2.902      -3.045    0.925        -0.990       0.213        5
        424.566       3.081      -1.202    0.923        0.513        -0.555       6
        534.758       2.856      -1.341    0.659        -0.676       -0.302       7
        580.964       2.485      -1.326    0.821        -0.489       -0.752       8
        587.521       3.568      -1.282    0.911        -0.537       -0.119       9
        725.016       3.999      -1.103    0.714        -0.653       -0.490       10
        736.495       2.808      -1.345    0.710        -0.996       -0.730       11
        746.529       3.200      -0.868    0.303        -0.376       -0.682       12
        757.672       3.172      -1.527    0.420        0.271        0.211        13
        768.768       2.830      -1.321    0.741        -0.842       -0.252       14
        799.199       2.696      -2.096    0.926        0.476        -0.511       15
        807.575       2.445      -4.136    0.745        0.171        -0.131       16


You can even pop this up in your web browser if that's a good format for you: ``photfile.show_in_browser()``. ``imexam`` has several functions to help display regions on the DS9 window. Since we have this data loaded into memory, the one we will use here is ``mark_region_from_array()``.

Let's make an array that the method will accept, namely a list of tuples which contain the (x,y,comment) that we want marked to the display. It will also accept any iterator containing a tuple of (x,y,comment).

::

    #lets make a list of our locations as a tuple of x,y,comment
    #we'll cut the list to a smaller area and only include those points whose mag is < -4.
    locations=list()
    for point in range(0,len(photfile['XCENTER']),1):
        if photfile['MAG'][point] < -4:
            locations.append((photfile['XCENTER'][point],photfile['YCENTER'][point],photfile['ID'][point]))

    #so the first item looks like:
    In [91]: locations[0]
    Out[91]: (807.57500000000005, 2.4449999999999998, 16)


Let's open up a DS9 window (if you haven't already) and display your image. This will let us display our source locations and play with them

::

    viewer=imexam.connect()
    viewer.load_fits('iabf01bzq_flt.fits')
    viewer.scale() #scale to DS9 zscale by default
    viewer.mark_region_from_array(locations)



.. image:: ../_static/iab_locations.png
    :height: 400
    :width: 600
    :alt: subsection of image being examined


Now we can get rid of some of the stars by hand and save a new file of locations we like. I did this arbitrarily because I decided I didn't like stars in this part of space. Click on the regions you don't want and delete them from the screen. You can even add more regions of your own choosing.


.. image:: ../_static/iab_badstars.png
    :height: 400
    :width: 600
    :alt: subsection of image being examined


You can save these new regions to a ``DS9`` style region file, either through ``DS9`` or ``imexam``

::

    viewer.save_regions('badstars.reg')

.. note:: A future version of the ``imexam`` package will make use of the region interpreter currently being developed with astropy for smoother creation and use of parsable regions files


Here is what the saved region file looks like, you can choose to import this file into any future DS9 display of the same image using the ``viewer.load_regions()`` method. You might also want to parse the file to save just the location and comment information in a separate text file.

::


    In [7]: !head badstars.reg
    # Region file format: DS9 version 4.1
    # Filename: /Users/sosey/ssb/sosey/testme/iabf01bzq_flt.fits[SCI]
    global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
    fk5
    circle(0:22:38.709,-72:02:50.58,0.677464")
    # text(0:22:39.097,-72:02:50.86) font="time 12 bold" text={ 16 }
    circle(0:22:36.340,-72:02:58.27,0.677464")
    # text(0:22:36.729,-72:02:58.55) font="time 12 bold" text={ 140 }
    circle(0:22:29.068,-72:03:20.78,0.677464")
    # text(0:22:29.457,-72:03:21.06) font="time 12 bold" text={ 225 }

                . . .

    # text(0:22:56.855,-72:04:23.16) font="time 12 bold" text={ 21985 }
    circle(0:22:42.791,-72:05:04.04,0.677464")
    # text(0:22:43.180,-72:05:04.32) font="time 12 bold" text={ 22002 }
    box(0:22:45.694,-72:04:19.19,14.593",13.1774",149.933) # color=red font="helvetica 16 normal roman" text={I DONT LIKE THE STARS HERE}


Advanced Usage II - Cycle through objects from a list
-----------------------------------------------------

This example will step through a list of object locations and center that object in the DS9 window with a narrow zoom so that you can examine it further (think about PSF profile creation options here..)


If you haven't already, start DS9 and load your image into the viewer. I'll assume that you started ``DS9`` outside of ``imexam`` and will need to connect to the window first.

::

    import imexam
    imexam.list_active_ds9()

        DS9 1396283378.28 gs 82a7e75f:53892 sosey

    viewer=imexam.connect('82a7e75f:53892')

    #A little unsure this is the correct window? Let's check by asking what image is loaded. The image I'm working with is iabf01bzq_flt.fits

    viewer.get_data_filename()

        '/Users/sosey/ssb/sosey/testme/iabf01bzq_flt.fits'  <-- notice it returned the full pathname to the file

    viewer.zoomtofit()  <-- let's zoom out  to see the whole image, incase just a small section was loaded


Read in your list of object locations, I'll use the same DAOphot targets from the previous example

::

    from astropy.io import ascii
    reader=ascii.Daophot()
    output_locations='iabf01bzq_stars.dat'
    photfile=reader.read(output_locations)

    #make some cuts on the list

    locations=list()
    for point in range(0,len(photfile['XCENTER']),1):
        if photfile['MAG'][point] < -4:
            locations.append((photfile['XCENTER'][point],photfile['YCENTER'][point],photfile['ID'][point])) <-- appending tuple to the list



Take your list of locations and cycle through each one, displaying a zoomed in section on the ``DS9`` window and starting ``imexam`` for each coordinate. I'm just going to go through 10 or so random stars. You can set this up however you like, including using a keystroke as your stopping condition in conjunction with ``viewer.readcursor()``

I'll also mark the object we're interested in on the display for reference

::

    viewer.zoom(8)
    for object in locations[100:110]:
        viewer.panto_image(object[0],object[1])
        viewer.mark_region_from_array(object)
        viewer.imexam()
