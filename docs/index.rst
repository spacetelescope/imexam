
.. image:: _static/imexam_workspace_ds9.png
    :height: 400
    :width: 600
    :alt: Example imexam workspace

The above image is an example desktop interfacing with DS9.


``imexam`` is an affiliated package of AstroPy. It was designed to be a lightweight library that enables users to explore data using common methods which are consistant across viewers.
The power of this python tool is that it is essentially a library of plotting
and analysis routines that can be directed towards any viewer. It attempts to
standardize the analysis interface so that no matter
what viewer is in use the calls and results are the same.  It can also be used
without connecting to any viewer since the calls take only data and location
information. This means that given a data array and a list of x,y positions
you can create plots and return information without having to interact with
the viewers, just by calling the functions directly either from a a command line
shell or from a private script.

``imexam`` can be used:

* from a command line interface
* through a Jupyter notebook or through a Jupyter console
* with multiple viewers, such as DS9 or Ginga (submit a github issue or PR to add others)
* without a viewer as a simple library to make plots and grab quick photometry information.


``imexam`` may be used as a replacement for the IRAF imexamine task. You should be able
to perform all of the most used functions that ``imexamine`` provided in IRAF, but
you also gain the flexibility of python and the ability to add your own analysis functions.
The standalone library has also been used as a replacement for ``psfmeasure``.

.. image:: _static/ginga_desktop_html5.png
    :height: 400
    :width: 600
    :alt: Example imexam workspace

The above image is an example desktop using the Jupyter notebook and the Ginga HTML5 viewer.



Installation
============

.. toctree::
   :maxdepth: 2

   Description <imexam/description.rst>


Simple Walkthrough
==================
.. toctree::
  :maxdepth: 2


  Getting started with a basic walk though a simple use case <imexam/walkthrough.rst>


User documentation
==================
.. toctree::
   :maxdepth: 2


    The imexam() Method <imexam/imexam_command.rst>
    Imexam User Methods <imexam/current_capability.rst>
    Convenience functions for the XPA <imexam/xpa_commands.rst>
    Examples <imexam/examples.rst>
    Dependencies <imexam/dependencies.rst>
    IRAF-imexamine Capabilites <imexam/iraf_imexam.rst>
    Comparison with IRAF <imexam/comparison_iraf.rst>


Reporting Issues
================

If you have found a bug in ``imexam`` please report it by creating a
new issue on the ``imexam`` `GitHub issue tracker
<https://github.com/spacetelescope/imexam/issues>`_.

Please include an example that demonstrates the issue sufficiently so that
the developers can reproduce and fix the problem. You may also be asked to
provide information about your operating system and a full Python
stack trace.  The developers will walk you through obtaining a stack
trace if it is necessary.


Contributing
============

Like the `Astropy <https://www.astropy.org/>`__ project, ``imexam`` is made both by and for its
users.  We accept contributions at all levels, spanning the gamut from
fixing a typo in the documentation to developing a major new feature.
We welcome contributors who will abide by the `Python Software
Foundation Code of Conduct
<https://www.python.org/psf/conduct/>`_.

``imexam`` follows the same workflow and coding guidelines as
`Astropy <https://www.astropy.org/>`__.  The following pages will help you get started with
contributing fixes, code, or documentation (no git or GitHub
experience necessary):

* `How to make a code contribution <https://docs.astropy.org/en/latest/development/workflow/development_workflow.html>`_

* `Coding Guidelines <https://docs.astropy.org/en/latest/development/codeguide.html>`_

* `Developer Documentation <https://docs.astropy.org/en/latest/#developer-documentation>`_

For the complete list of contributors please see the `imexam
contributors page on Github
<https://github.com/spacetelescope/imexam/graphs/contributors>`_.

Reference API
=============
.. toctree::
   :maxdepth: 1

   imexam/reference_api.rst
