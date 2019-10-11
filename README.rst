Welcome to nxstools's documentation!
====================================

Authors: Jan Kotanski

------------
Introduction
------------

Configuration tools for NeXDaTaS Tango Servers consists of the following command-line scripts:

- `nxscollect <https://nexdatas.github.io/tools/nxscollect.html>`__ uploads external images into the NeXus/HDF5 file
- `nxsconfig <https://nexdatas.github.io/tools/nxsconfig.html>`__ reads NeXus Configuration Server settings
- `nxscreate <https://nexdatas.github.io/tools/nxscreate.html>`__ creates NeXus Configuration components
- `nxsdata <https://nexdatas.github.io/tools/nxsdata.html>`__ runs NeXus Data Writer
- `nxsfileinfo <https://nexdatas.github.io/tools/nxsfileinfo.html>`__ shows nedadata of the NeXus/HDF5 file
- `nxsetup <https://nexdatas.github.io/tools/nxsetup.html>`__ setups NeXDaTaS Tango Server environment

as well as the `nxstools <https://nexdatas.github.io/tools/nxstools.html>`__ package which allows perform these operations
directly from a python code.

| Source code: https://github.com/nexdatas/tools
| Web page: https://nexdatas.github.io/tools
| NexDaTaS Web page: https://nexdatas.github.io

------------
Installation
------------

Install the dependencies:

|    PyTango, sphinx

From sources
""""""""""""

Download the latest NXS Tools version from

|    https://github.com/nexdatas/tools

Extract sources and run

.. code-block:: console

	  $ python setup.py install

Debian packages
"""""""""""""""

Debian `stretch`, `jessie` (and `wheezy`)  or Ubuntu `bionic` (and `xenial`) packages can be found in the HDRI repository.

To install the debian packages, add the PGP repository key

.. code-block:: console

	  $ sudo su
	  $ wget -q -O - http://repos.pni-hdri.de/debian_repo.pub.gpg | apt-key add -

and then download the corresponding source list

.. code-block:: console

	  $ cd /etc/apt/sources.list.d
	  $ wget http://repos.pni-hdri.de/stretch-pni-hdri.list

For releases (>= 2.61.0) to insall python2 scripts

.. code-block:: console

	  $ apt-get update
	  $ apt-get install nxstools

and for python3 scripts

.. code-block:: console

	  $ apt-get update
	  $ apt-get install nxstools3


For older releases

.. code-block:: console

	  $ apt-get update
	  $ apt-get install python-nxstools

and

.. code-block:: console

	  $ apt-get install python3-nxstools

if exists.

To instal other NexDaTaS packages

.. code-block:: console

	  $ apt-get install python-nxswriter nxsconfigserver-db python-nxsconfigserver nxsconfigtool

and

.. code-block:: console

	  $ apt-get install python-nxsrecselector nxselector python-sardana-nxsrecorder

for Component Selector and Sardana related packages.

From pip
""""""""

To install it from pip you can

.. code-block:: console

   $ python3 -m venv myvenv
   $ . myvenv/bin/activate

   $ pip install nxstools

Moreover it is also good to install

.. code-block:: console

   $ pip install pytango
