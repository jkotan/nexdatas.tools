Welcome to nxstools's documentation!
====================================

Authors: Jan Kotanski

------------
Introduction
------------

Configuration tools for NeXDaTaS Tango Servers consists of the following command-line scripts:
  - **nxscollect** uploads external images into NeXus/HDF5 file
  - **nxsconfig** reads NeXus Configuration Server settings
  - **nxscreate** creates NeXus Configuration components
  - **nxsdata** runs NeXus Data Writer
  - **nxsetup** setups NeXDaTaS Tango Server environment

as well as the **nxstools** package which allows perform these operations
directly from a python code.

| Source code: https://github.com/nexdatas/tools
| Web page: http://www.desy.de/~jkotan/nxstools

------------
Installation
------------

Install the dependencies:

    PyTango, sphinx

From sources
""""""""""""

Download the latest NXS Tools version from

    https://github.com/jkotan/nexdatas.tools/

Extract sources and run

.. code:: bash
	  
	  $ python setup.py install

Debian packages
"""""""""""""""

Debian Jessie (and Wheezy) packages can be found in the HDRI repository.

To install the debian packages, add the PGP repository key

.. code:: bash

	  $ sudo su
	  $ wget -q -O - http://repos.pni-hdri.de/debian_repo.pub.gpg | apt-key add -

and then download the corresponding source list

.. code:: bash

	  $ cd /etc/apt/sources.list.d
	  $ wget http://repos.pni-hdri.de/jessie-pni-hdri.list

Finally,

.. code:: bash

	  $ apt-get update
	  $ apt-get install python-nxstools

To instal other NexDaTaS packages	  

.. code:: bash
	  
	  $ apt-get install python-nxswriter nxsconfigserver-db python-nxsconfigserver nxsconfigtool

and 

.. code:: bash

	  $ apt-get install python-nxsrecselector nxselector python-sardana-nxsrecorder

for Component Selector and Sardana related packages.
