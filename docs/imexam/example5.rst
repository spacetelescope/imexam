
=========
Example 5
=========

Use the imexamine library standalone to create plots without viewing
--------------------------------------------------------------------

It's possible to use the imexamine library of plotting functions without loading
an image into the viewer. All of the functions take 3 inputs: the x, y, and data
array. In order to access the function, first create an imexamine object:

::

    from imexam.imexamine import Imexamine
    import numpy as np

    data=np.random.rand((100,100)) #create a random array thats 100x100 pixels
    plots=Imexamine()


These are the functions you now have access to:

::

        plots.aper_phot                 plots.contour_plot              plots.histogram_plot            plots.plot_line                 plots.set_colplot_pars          plots.set_surface_pars
        plots.aperphot_def_pars         plots.curve_of_growth_def_pars  plots.imexam_option_funcs       plots.plot_name                 plots.set_column_fit_pars       plots.show_xy_coords
        plots.aperphot_pars             plots.curve_of_growth_pars      plots.line_fit                  plots.print_options             plots.set_contour_pars          plots.showplt
        plots.colplot_def_pars          plots.curve_of_growth_plot      plots.line_fit_def_pars         plots.register                  plots.set_data                  plots.sleep_time
        plots.colplot_pars              plots.do_option                 plots.line_fit_pars             plots.report_stat               plots.set_histogram_pars        plots.surface_def_pars
        plots.column_fit                plots.gauss_center              plots.lineplot_def_pars         plots.report_stat_def_pars      plots.set_line_fit_pars         plots.surface_pars
        plots.column_fit_def_pars       plots.get_options               plots.lineplot_pars             plots.report_stat_pars          plots.set_lineplot_pars         plots.surface_plot
        plots.column_fit_pars           plots.get_plot_name             plots.new_plot_window           plots.reset_defpars             plots.set_option_funcs          plots.unlearn_all
        plots.contour_def_pars          plots.histogram_def_pars        plots.option_descrip            plots.save_figure               plots.set_plot_name
        plots.contour_pars              plots.histogram_pars            plots.plot_column               plots.set_aperphot_pars         plots.set_radial_pars



To create a plot, just specify the method:

::

    plots.plot_line(10,10,data)

produces the following plot:

.. image:: ../_static/imexamine_library_lineplot.png
    :height: 400
    :width: 400
    :alt: line plot generated without viewing


You can then save the current plot using the save method:

::

    plots.contour(10,10,data)
    plots.save() # with an optional filename using filename="something.extname"

    In [1]: plots.plot_name
    Out[2]: 'imexam.pdf'

    plots.close() # close the plot window

Where the extname specifies the format of the file, ex: jpg or pdf. A pdf file will be the default output, using the curent self.plot_name.

.. image:: ../_static/example_5a.png
    :height: 400
    :width: 400
    :alt: contour plot generated without viewing

Note that no name is attached to the above contour plot because we plotted a data array. When you are using the plotting class without a viewer, you can attach any title you like by editing the plotting parameters using the dictionary directly:::

    plots.contour_pars['title'][0] = "random numpy array"


.. image:: ../_static/example_5b.png
    :height: 400
    :width: 400
    :alt: contour plot generated without viewing and title


Return information to variables without plotting
------------------------------------------------

Some of the imexamine() methods are capable of returning their results as data objects.
First, lets import some useful things to use in the examples: ::


    from astropy.io import fits
    from imexam.imexamine import Imexamine

    # get my example data from a fits image
    data=fits.getdata()


Return the fitting result for a line (the same can be done for column_fit): ::


    In [1]: plots.line_fit(462, 377, data, genplot=False)
    using model: <class 'astropy.modeling.functional_models.Gaussian1D'>
    Name: Gaussian1D
    Inputs: ('x',)
    Outputs: ('y',)
    Fittable parameters: ('amplitude', 'mean', 'stddev')
    xc=462.438219	yc=377.038640
    Out[1]: <Gaussian1D(amplitude=512.5638896303021, mean=462.45102207881393, stddev=-0.6638566150545719)>

    # I could have specified an output object here instead and saved the model object:

    In [1]: results = plots.line_fit(462, 377, data, genplot=False)
    using model: <class 'astropy.modeling.functional_models.Gaussian1D'>
    Name: Gaussian1D
    Inputs: ('x',)
    Outputs: ('y',)
    Fittable parameters: ('amplitude', 'mean', 'stddev')
    xc=462.438219	yc=377.038640

    In [2]: results
    Out[2]: <Gaussian1D(amplitude=512.5638896303021, mean=462.45102207881393, stddev=-0.6638566150545719)>

    In [3]: type(results)
    Out[3]:
    <class 'astropy.modeling.functional_models.Gaussian1D'>
    Name: Gaussian1D
    Inputs: ('x',)
    Outputs: ('y',)
    Fittable parameters: ('amplitude', 'mean', 'stddev')

Return the radial profile data points: ::

    In [1]: results = plots.radial_profile(462, 377, data, genplot=False)
    xc=462.438220	yc=377.038640

    # here, results is a tuple of the radius and the flux arrays
    In [2]: type(results)
    Out[2]: tuple

    In [3]: results
    Out[3]:
    (array([ 0.43991986,  0.56310764,  1.05652729,  1.11346785,  1.12730166,
             1.18083435,  1.4387386 ,  1.56225828,  1.72993907,  1.77404857,
             1.83394967,  1.8756147 ,  2.00971898,  2.0402282 ,  2.08520709,
             2.11462747,  2.43216151,  2.43852579,  2.49490037,  2.50720797,
             2.56207175,  2.56811411,  2.62090222,  2.65022406,  2.73622589,
             2.76432473,  2.99360832,  3.0141751 ,  3.07007625,  3.09013412,
             3.12919301,  3.17820187,  3.22639932,  3.27395339,  3.29213154,
             3.34795643,  3.36181609,  3.41650254,  3.43843675,  3.56198995,
             3.57009352,  3.59167466,  3.68924014,  3.71012829,  3.83595742,
             3.89592694,  3.91565741,  3.95831886,  3.97442453,  3.98552521,
             3.9971748 ,  4.00099637,  4.0623451 ,  4.06610542,  4.0775248 ,
             4.10394097,  4.21436241,  4.25811375,  4.28708374,  4.33010037,
             4.43838783,  4.53773166,  4.541146  ,  4.55813187,  4.56194401,
             4.58853854,  4.63205502,  4.65159003,  4.66197958,  4.67852677,
             4.68183843,  4.71753044,  4.71757631,  4.78260702,  4.85229095,
             4.88403989,  4.96555878,  4.98067583,  4.99306443,  4.99658806,
             5.05766026,  5.06986075,  5.16561429,  5.20137031,  5.2398823 ,
             5.24535309,  5.27513495,  5.30395753,  5.32716192,  5.33548947,
             5.37876614,  5.3848761 ,  5.43835691,  5.43870338,  5.48116519,
             5.52253984,  5.52811091,  5.53651564,  5.56191459,  5.58370969,
             5.59757142,  5.64425498,  5.65248702,  5.65793014,  5.78110428,
             5.80777797,  5.89748546,  5.92363512,  5.94896363,  5.97744528,
             5.98777194,  6.00070036,  6.03626122,  6.04170629,  6.05451954,
             6.06471496,  6.09265553,  6.09993812,  6.10748513,  6.13239687,
             6.16254603,  6.17042707,  6.19224411,  6.20754751,  6.22957178,
             6.23733343,  6.30103604,  6.33772298,  6.43833558,  6.44070886,
             6.48849245,  6.50959949,  6.51230262,  6.52146032,  6.5595647 ,
             6.56189413,  6.63183044,  6.64347305,  6.65679268,  6.71458743,
             6.72804634,  6.73034962,  6.73980232,  6.75327507,  6.77383526,
             6.79689127,  6.82830694,  6.84864187,  6.87117266,  6.87342797,
             6.8817999 ,  6.94435706,  6.9488506 ,  6.97513961,  6.98399121,
             7.01080949,  7.08663012,  7.10837617,  7.11926989,  7.13440215,
             7.19907049,  7.23120275,  7.3613401 ,  7.37600509,  7.41364442,
             7.41776616,  7.43206628,  7.45308634,  7.49419535,  7.50475127,
             7.50650756,  7.55930201,  7.56802554,  7.60008443,  7.66481157,
             7.70503555,  7.76414132,  7.81964293,  8.06920371,  8.12646314,
             8.12808509,  8.15298819,  8.17548548,  8.20966328,  8.22630274,
             8.25580581,  8.27314042,  8.32288269,  8.77430839,  8.8269951 ,
             8.83372905,  8.86536955,  8.91032754,  8.91751826,  9.48215209,
             9.56647781]),
     array([ 408.87057495,   41.23228073,   91.90717316,   48.38606262,
             112.11755371,   64.6014328 ,  361.9876709 ,    7.88528776,
              76.15605927,   92.4905777 ,    5.74170589,    8.54299355,
              37.25744629,   17.17868423,   41.94879532,   29.16669464,
              25.11438942,   41.24355316,   31.41527748,    2.35880852,
               2.51266503,    3.61639667,   31.96870041,   47.24103928,
               1.86882472,    2.25345397,    3.43679786,    2.95230484,
               7.01711893,    4.25243187,   10.45163536,   15.06377506,
               2.06799817,    1.55962014,    3.2355001 ,    3.58886528,
               4.77823544,    2.61030412,    6.15013599,    2.26734257,
               3.79847336,    5.18475103,    2.02961087,    1.86825836,
               2.26850033,    1.98072493,    2.40412855,    2.35658216,
               2.2638216 ,    1.48555958,    2.15530491,    1.40320516,
               2.42260337,    3.59516048,    1.49309242,    2.70001984,
               1.35936797,    2.50372696,    1.99834633,    2.1075139 ,
               2.10088921,    3.91031456,    1.40116227,    1.58724546,
               1.64244962,    4.27553177,    2.86458731,    2.07594514,
               1.24715221,    1.55571783,    3.28257489,    1.08224833,
               1.99108934,    1.28673184,    2.22391272,    2.01411462,
               1.27933741,    2.57424259,    2.27977562,    1.34119225,
               2.46366167,    2.04145074,    2.27879167,    3.32902098,
               2.0256803 ,    3.04667783,    3.214293  ,    2.71672273,
               1.18290937,    3.39013147,    2.61141396,    1.24552131,
               2.7109127 ,    1.20734   ,    1.065956  ,    2.0110569 ,
               2.63785267,    2.08804011,    1.23607028,    1.53105474,
               2.9585526 ,    0.92856985,    1.70498252,    0.98702717,
               3.00484014,    2.96310997,    1.10799265,    1.02301562,
               2.59040713,    1.55507016,    1.1307373 ,    1.46614468,
               3.7729485 ,    0.8989926 ,    1.81300449,    1.49930847,
               0.97070342,    3.58096623,    1.45315814,    1.37846851,
               1.22037327,    2.02710581,    3.06499743,    1.60018504,
               3.15293145,    1.34511912,    1.04039967,    0.94602752,
               1.5991565 ,    1.11648059,    0.90265507,    1.25119698,
               1.32048595,    1.331002  ,    1.26167858,    0.81102282,
               0.99124312,    0.76625013,    1.42264056,    1.41574192,
               1.67775941,    1.15894651,    1.19685972,    0.99676919,
               1.16761708,    1.20492256,    1.09948123,    1.0989542 ,
               0.92135239,    0.89912277,    1.15777898,    1.07870626,
               1.32945871,    1.06859183,    0.77524334,    1.4281857 ,
               1.05790067,    1.08861005,    1.03711545,    1.00277674,
               1.11795783,    1.04079187,    1.77855933,    0.875655  ,
               1.70616186,    0.95955884,    1.2846061 ,    0.9819802 ,
               1.09096873,    1.12618971,    2.52278042,    1.14947557,
               2.55132389,    1.16845107,    1.0366509 ,    1.03310716,
               0.76811701,    0.98454052,    1.38449657,    1.41319823,
               1.30402267,    1.26531458,    0.88282102,    1.33250594,
               0.86149669,    1.13119161,    0.89653128,    1.47101414,
               2.82045436,    2.37812138,    0.82307637,    1.3075676 ,
               1.45813155,    1.30278611,    1.60565269,    1.01857305], dtype=float32))


Return the curve of growth points: ::

    In [1]: results = plots.curve_of_growth(462, 377, data, genplot=False)
    xc=462.438220	yc=377.038640

    at (x,y)=462,377
    radii:[1 2 3 4 5 6 7 8]
    flux:[406.65712375514534, 1288.8955810496341, 1634.0235081082126, 1684.5579429185905, 1718.118845192796, 1785.265260722455, 1801.8561084128257, 1823.21222063562]

    In [2]: type(results)
    Out[2]: tuple

    In [3]: results
    Out[3]:
    (array([1, 2, 3, 4, 5, 6, 7, 8]),
     [406.65712375514534,
      1288.8955810496341,
      1634.0235081082126,
      1684.5579429185905,
      1718.118845192796,
      1785.265260722455,
      1801.8561084128257,
      1823.21222063562])

     # the typle can be separated into it's parts
     radius, flux = results


Return the histogram information as a tuple of values and bin edges: ::

    In [1]: counts, bins = plots.histogram(462, 377, data, genplot=False)

    In [2]: counts
    Out[2]:
    array([372,   7,   1,   1,   1,   0,   1,   3,   1,   2,   1,   2,   0,
              0,   0,   1,   0,   0,   1,   0,   0,   0,   2,   0,   0,   0,
              0,   1,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
              0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
              0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
              0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
              0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   0,   0,
              0,   0,   0,   0,   0,   0,   0,   0,   0]

    In [3]: bins
    Out [3]:
     array()[   0.58091092,    4.66380756,    8.7467042 ,   12.82960084,
              16.91249748,   20.99539412,   25.07829076,   29.1611874 ,
              33.24408404,   37.32698068,   41.40987732,   45.49277396,
              49.5756706 ,   53.65856725,   57.74146389,   61.82436053,
              65.90725717,   69.99015381,   74.07305045,   78.15594709,
              82.23884373,   86.32174037,   90.40463701,   94.48753365,
              98.57043029,  102.65332693,  106.73622357,  110.81912021,
             114.90201685,  118.98491349,  123.06781013,  127.15070677,
             131.23360341,  135.31650005,  139.39939669,  143.48229333,
             147.56518997,  151.64808661,  155.73098325,  159.81387989,
             163.89677653,  167.97967317,  172.06256981,  176.14546645,
             180.22836309,  184.31125973,  188.39415637,  192.47705302,
             196.55994966,  200.6428463 ,  204.72574294,  208.80863958,
             212.89153622,  216.97443286,  221.0573295 ,  225.14022614,
             229.22312278,  233.30601942,  237.38891606,  241.4718127 ,
             245.55470934,  249.63760598,  253.72050262,  257.80339926,
             261.8862959 ,  265.96919254,  270.05208918,  274.13498582,
             278.21788246,  282.3007791 ,  286.38367574,  290.46657238,
             294.54946902,  298.63236566,  302.7152623 ,  306.79815894,
             310.88105558,  314.96395222,  319.04684886,  323.1297455 ,
             327.21264215,  331.29553879,  335.37843543,  339.46133207,
             343.54422871,  347.62712535,  351.71002199,  355.79291863,
             359.87581527,  363.95871191,  368.04160855,  372.12450519,
             376.20740183,  380.29029847,  384.37319511,  388.45609175,
             392.53898839,  396.62188503,  400.70478167,  404.78767831,
             408.87057495])
