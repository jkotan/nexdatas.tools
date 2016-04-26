Welcome to nxstools's documentation!
====================================

Authors: Jan Kotanski, Eugen Wintersberger, Halil Pasic
Introduction

Configuration tools for NeXDaTaS Tango Servers

consists of the following command-line scripts:
  - **nxscollect** to upload external images into NeXus/HDF5 file
  - **nxsconfig** to read NeXus Configuration Server settings
  - **nxscreate** to create NeXus Configuration components
  - **nxsdata** to run NeXus Data Writer
  - **nxsetup** to setup NeXDaTaS Tango Server environment
as well as the **nxstools** package which allows perform these operations
directly from a python code.

-------------------------
Installation from sources
-------------------------

Install the dependencies:

    PyTango

Download the latest NXS Tools version from

    https://github.com/jkotan/nexdatas.tools/

Extract sources and run

$ python setup.py install


Contents
========

.. toctree::
   :maxdepth: 4

   nxscollect
   nxsconfig
   nxscreate
   nxsdata
   nxsetup
   nxstools

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

