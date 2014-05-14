========================
imexam analysis commands
========================

close():
    close the DS9 window and end the connection

view(img, header=None, frame=None, asFits=False): 
    Load an image array into a DS9 frame, if no frame is specified, the current frame is used. If no frame exists, then a new one is created.
    A basic header is created and sent to DS9. You can look at this header with disp_header() but get_header() will return an error because it 
    looks for a filename, and no file was loaded, just the array.

readcursor(): 
    returns image coordinate postion and key pressed as a tuple of the for float(x), float(y), str(key)

make_region(infile,doLabels=False): 
    make an input reg file with  [x,y,comment] to a view specific reg file, the input file should contain lines with x,y,comment    

    infile: str
        input filename

    labels: bool
        add labels to the regions

    header: int
        number of header lines in text file to skip

    textoff: int
        offset in pixels for labels

    rtype: str
        region type, one of the acceptable ds9 regions

    size: int
        size of the region type

mark_region_from_array(input_points,rtype="circle",ptype="image",textoff=10,size=5):
    mark regions on the display given a list of tuples, a single tuple, or a string, where each object has x,y,comment specified

    input_points: a tuple, or list of tuples, or a string: (x,y,comment), 


    ptype: string
        the reference system for the point locations, image|physical|fk5
    rtype: string
        the matplotlib style marker type to display
    size: int
        the size of the region marker

    textoff: string
        the offset for the comment text, if comment is empty it will not show
    
unlearn():
    reset all the imexam default parameters

imexam(): 
    access realtime imexamine functions through the keyboard and mouse

**Current recognized keys for use during imexam are**::

         'a': 'aperture sum, with radius region_size, optional sky subtraction ',
         'j': '1D  line fit ',
         'k': '1D  column fit ',
         'm': 'square region stats, in region_size square, default stat is median',
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
         '2': 'make the next plot in a new window'
         
         aimexam(): return a dict of current parameters for aperture photometery
         
         cimexam(): return dict of current parameters for column plots

         eimexam(): return dict of current parameters for contour plots

         himexam(): return dict current parameters for histogram plots

         jimexam(): return dict current parameters for 1D gaussian line plots

         kimexam(): return dict of current parameters for 1D gaussian column plots

         limexam(): return dict of current parameters for  line plots

         rimexam(): return dict of current parameters for curve of growth plots

         wimexam(): return dict of current parameters for surface plots
    
         mimexam(): return dict of current parameters for area statistics
         
        
.. note:: Some of the plots accept a marker type, any valid Matplotlib marker may be specified. See this page for the full list: http://matplotlib.org/api/markers_api.html#module-matplotlib.markers   
 
        
The imexam key dictionary is stored inside the user object as  <object_name>.exam.imexam_option_funcs{}. Each key in the dictionary is the key to recognize from the user, it's associated value is a tuple which contains the name of the function to call and a description of what that function does. "q" is always assumed to be the returned key when the user wishes to quit interaction with the window. Users may change the default settings for each of the imexamine recognized keys by editing the associated dictionary. You can either edit it directly, by accessing each of the values by their keyname, or save a copy of the dictionary ( for example: mydict= object.aimexam(); then reset mydict to values you prefer, and set object.exam.aperphot_pars = mydict)

Users may also add their own imexam keys and associated functions by registering them with the connect.register(user_funct=dict()) method. The new binding will bew added to the dictionary of imexamine functions as long as the key is unique. The new functions do not have to have default dictionaries association with them.

Circular Apterture Photometry
-----------------------------

Aperture photometry is currently implemented using the photutils python package, which is an affiliated package of astropy that is still in development.

Currently, the calculation which is performed is similar to the "," IRAF key. It is circular aperture photometry, centered on the mouse location at the time the key is pressed, with a background annulus subtraction for the sky. The radius of the aperture is set with the regsion_size keyword (default to 5 pixels). The annulus size is also set to the width, and taken a distance of skyrad pixels from the center. The pixels used to calculate the enclosed flux are those whose centers fall inside the radius distance, in the same way that IRAF imexamine computes the flux.

::

    aperphot_pars= {"function":["aperphot",],
                    "center":[True,"Center the object location using a 2d gaussian fit"],
                    "width":[5,"Width of sky annulus in pixels"],
                    "subsky":[True,"Subtract a sky background?"],
                    "skyrad":[15,"Distance to start sky annulus is pixels"],
                    "radius":[5,"Radius of aperture for star flux"],
                    "zmag":[25.,"zeropoint for the magnitude calculation"],                
                    }



Median square region stats
--------------------------
The  pixel values around the pointer location are calculated inside a box which has a side equal to the region_size, defaulted to 5 pixels, and using the statistical function chosen.
The user can map the function to any reasonable numpy function, it's set to numpy.median by default

::

    report_stat_pars= {"function":["report_stat",],
                        "stat":["median","which numpy stat to return [median,min,max...must map to numpy func]"],
                        "region_size":[5,"region size in pixels to use"],
                    }

Line or Column plots
--------------------
Display a plot of the points through either the line or column closest to the cursor location.

.. image:: column_plot.png
    :height: 400
    :width: 600
    :alt: Column plot

.. image:: line_plot.png
    :height: 400
    :width: 600
    :alt: Line plot



Curve of Growth plot
--------------------
This displays a curve of growth for the flux around the current pointer location in successively larger radii. If centering is on, the center is computed close to the star using a 2d gaussian. 

::
    
    curve_of_growth_plot(x,y)

    curve_of_growth_pars={"function":["curve_of_growth_plot",],
                              "title":["Curve of Growth","Title of the plot"],
                              "xlabel":["radius","The string for the xaxis label"],
                              "ylabel":["Flux","The string for the yaxis label"],
                              "center":[True,"Solve for center using 2d Gaussian? [bool]"],
                              "background":[True,"Fit and subtract background? [bool]"],
                              "buffer":[25.,"Background inner radius in pixels,from center of star"],
                              "width":[5.,"Background annulus width in pixels"],
                              "magzero":[25.,"magnitude zero point"],
                              "rplot":[8.,"Plotting radius in pixels"],
                              "pointmode":[True,"plot points instead of lines? [bool]"],
                              "marker":["o","The marker character to use, matplotlib style"],
                              "logx":[False,"log scale x-axis?"],
                              "logy":[False,"log scale y-axis?"],
                              "minflux":[0., "only measure flux above this value"],
                              }


.. image:: radial_profile.png
    :height: 400
    :width: 600
    :alt: Curve of growth  plot around star



1D Gaussian or Moffat profile
-----------------------------
A 1D gaussian profile is fit to the data in either the line or column of the current pointer location. A plot of both the data and the fit + parameters is displayed.
If the centering option is True, then the center of the flux is computed by fitting a 2d Gaussian to the data.

::
    
    line_fit(x,y,form,delta=20) # where form is the function to fit, Gaussian or Moffat
    
    
    line_fit_pars={"function":["line_fit",],
                             "func":["gaussian","function for fitting [gaussian|moffat]"],
                             "title":["Fit 1D line plot","Title of the plot"],
                             "xlabel":["Line","The string for the xaxis label"],
                             "ylabel":["Flux","The string for the yaxis label"],
                             "background":[False,"Solve for background? [bool]"],
                             "width":[10.0,"Background  width in pixels"],
                             "xorder":[0,"Background terms to fit, 0=median"],
                             "rplot":[20.,"Plotting radius in pixels"],
                             "pointmode":[True,"plot points instead of lines? [bool]"],
                             "logx":[False,"log scale x-axis?"],
                             "logy":[False,"log scale y-axis?"],
                             "center":[True,"Recenter around the local max"],
                             }

    column_fit(x,y,form,delta=20)

    column_fit_pars={"function":["column_fit",],
                                 "func":["gaussian","function for fitting [gaussian|moffat]"],
                                 "title":["Fit 1D column plot","Title of the plot"],
                                 "xlabel":["Column","The string for the xaxis label"],
                                 "ylabel":["Flux","The string for the yaxis label"],
                                 "background":[False,"Solve for background? [bool]"],
                                 "width":[10.0,"Background  width in pixels"],
                                 "xorder":[0,"Background terms to fit, 0=median"],
                                 "rplot":[20.,"Plotting radius in pixels"],
                                 "pointmode":[True,"plot points instead of lines? [bool]"],
                                 "logx":[False,"log scale x-axis?"],
                                 "logy":[False,"log scale y-axis?"],
                                 "center":[True,"Recenter around the local max"],
                                 }
    
    
.. image:: fit_line.png
    :height: 400
    :width: 600
    :alt: Plot of gaussian profile fit to data



Contour Plots
-------------

Display a contour plot around the clicked pixel location.

::
    
    contour_plot(x,y)

    contour_pars={"function":["contour",],
                       "title":["Contour plot in region around pixel location","Title of the plot"],
                       "xlabel":["x","The string for the xaxis label"],
                       "ylabel":["y","The string for the yaxis label"],
                       "ncolumns":[15,"Number of columns"],
                       "nlines":[15,"Number of lines"],
                       "floor":[None,"Minimum value to be contoured"],
                       "ceiling":[None,"Maximum value to be contoured"],
                       "ncontours":[8,"Number of contours to be drawn"],
                       "linestyle":["--","matplotlib linestyle"],
                       "label":[True,"Label major contours with their values? [bool]"],
                       "cmap":["jet","Colormap (matplotlib style) for image"],
                       }


.. image:: contour_plot.png
    :height: 400
    :width: 600
    :alt: contour plot
    

Histogram Plots
---------------

Display a histogram of pixel values around the clicked pixel location

::
    
    histogram_plot(x,y)

    histogram_pars={"function":["histogram",],
                       "title":["Histogram","Title of the plot"],
                         "xlabel":["Flux (bin)","The string for the xaxis label"],
                         "ylabel":["Count","The string for the yaxis label"],
                         "ncolumns":[21,"Number of columns"],
                         "nlines":[21,"Number of lines"],
                         "nbins":[100,"Number of bins"],
                         "z1":[None,"Minimum histogram intensity"],
                         "z2":[100,"Maximum histogram intensity"],
                         "pointmode":[True,"plot points instead of lines? [bool]"],
                         "marker":["o","The marker character to use, matplotlib style"],
                         "logx":[False,"log scale x-axis?"],
                         "logy":[False,"log scale y-axis?"],
                         }


.. image:: histogram_plot.png
    :height: 400
    :width: 600
    :alt: histogram plot


Surface Plots
-------------

Display a 3D surface plot of pixel values around the clicked pixel location


::
    
    surface_plot(x,y)

    surface_pars={"function":["surface",],
                       "title":["Surface plot","Title of the plot"],
                       "xlabel":["X","The string for the xaxis label"],
                       "ylabel":["Y","The string for the yaxis label"],
                       "zlabel":[None,"Label for zaxis"],
                       "ncolumns":[21,"Number of columns"],
                       "nlines":[21,"Number of lines"],
                       "azim":[None,"azimuthal viewing angle in degrees"],
                       "floor":[None,"Minimum value to be contoured"],
                       "ceiling":[None,"Maximum value to be contoured"],
                       "stride":[2,"step size, higher vals will have less contour"],
                       "cmap":["jet","colormap (matplotlib) for display"],
                       "fancy":[False,"This aint your grandpas iraf"],
                       }


.. image:: surface_plot.png
    :height: 600
    :width: 800
    :alt: surface plot

Or, if you'd like to get fancy

.. image:: fancy_surface.png
    :height: 600
    :width: 800
    :alt: fancy surface plot

